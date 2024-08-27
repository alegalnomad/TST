import 'dart:async';
import 'dart:io';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:image/image.dart' as img;
import 'package:exif/exif.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:file_picker/file_picker.dart';

late List<CameraDescription> cameras;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    cameras = await availableCameras();
  } on CameraException catch (e) {
    debugPrint('Error in fetching the cameras: $e');
  }
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: ThemeData.dark(),
      home: const TakePictureScreen(),
    );
  }
}

class TakePictureScreen extends StatefulWidget {
  const TakePictureScreen({super.key});

  @override
  State<TakePictureScreen> createState() => TakePictureScreenState();
}

class TakePictureScreenState extends State<TakePictureScreen> with WidgetsBindingObserver {
  CameraController? _controller;
  bool _isCameraInitialized = false;
  FlashMode _flashMode = FlashMode.off;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return;
    }
    if (state == AppLifecycleState.inactive) {
      _disposeCamera();
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera();
    }
  }

  Future<void> _disposeCamera() async {
    if (_controller != null) {
      await _controller!.dispose();
      _controller = null;
    }
    if (mounted) {
      setState(() {
        _isCameraInitialized = false;
      });
    }
  }

  Future<void> _initializeCamera() async {
    if (_controller != null) {
      await _disposeCamera();
    }

    if (cameras.isEmpty) {
      setState(() {
        _isCameraInitialized = false;
      });
      return;
    }

    final camera = cameras.first;
    _controller = CameraController(
      camera,
      ResolutionPreset.high,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );

    try {
      await _controller!.initialize();
      await _controller!.lockCaptureOrientation(DeviceOrientation.portraitUp);
      await _controller!.setFlashMode(_flashMode);
      if (mounted) {
        setState(() {
          _isCameraInitialized = true;
        });
      }
    } on CameraException catch (e) {
      debugPrint('Error initializing camera: $e');
      setState(() {
        _isCameraInitialized = false;
      });
    }
  }

  Future<void> _toggleFlash({bool forceOff = false}) async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    try {
      FlashMode newMode;
      if (forceOff) {
        newMode = FlashMode.off;
      } else {
        newMode = _flashMode == FlashMode.off ? FlashMode.torch : FlashMode.off;
      }

      await _controller!.setFlashMode(newMode);

      setState(() {
        _flashMode = newMode;
      });
    } catch (e) {
      debugPrint('Error toggling flash: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to toggle flash: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: _isCameraInitialized
          ? Stack(
              alignment: Alignment.center,
              children: [
                CameraPreview(_controller!),
                CustomPaint(
                  painter: OverlayPainter(),
                  child: Container(),
                ),
                Positioned(
                  top: MediaQuery.of(context).size.height * 0.3,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      "Ensure the test site is within the highlighted box",
                      style: TextStyle(color: Colors.white, fontSize: 16),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
              ],
            )
          : const Center(child: CircularProgressIndicator()),
      floatingActionButton: _isCameraInitialized
          ? Padding(
              padding: const EdgeInsets.only(bottom: 16.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Spacer(),
                  FloatingActionButton(
                    heroTag: "toggleFlash",
                    onPressed: _toggleFlash,
                    child: Icon(
                      _flashMode == FlashMode.torch ? Icons.flash_on : Icons.flash_off,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 16),
                  SizedBox(
                    width: 80,
                    height: 80,
                    child: FloatingActionButton(
                      heroTag: "takePicture",
                      onPressed: () async {
                        try {
                          final image = await _controller!.takePicture();
                          await _toggleFlash(forceOff: true);
                          final croppedImage = await cropTo800x600(image.path);
                          if (!mounted) return;
                          await Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (context) => DisplayPictureScreen(imagePath: croppedImage),
                            ),
                          );
                          _initializeCamera();
                        } catch (e) {
                          debugPrint('Error taking picture: $e');
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Failed to take picture: $e')),
                            );
                          }
                        }
                      },
                      child: const Icon(Icons.camera_alt, size: 48),
                    ),
                  ),
                  const Spacer(),
                ],
              ),
            )
          : null,
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }
}

class OverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black.withOpacity(0.5)
      ..style = PaintingStyle.fill;
    const cropWidth = 790;
    const cropHeight = 590;
    const aspectRatio = cropWidth / cropHeight;

    final rectWidth = size.width * 0.8;
    final rectHeight = rectWidth / aspectRatio;
    final left = (size.width - rectWidth) / 2;
    final top = (size.height - rectHeight) / 2;

    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, top), paint);
    canvas.drawRect(Rect.fromLTWH(0, top + rectHeight, size.width, size.height - top - rectHeight), paint);
    canvas.drawRect(Rect.fromLTWH(0, top, left, rectHeight), paint);
    canvas.drawRect(Rect.fromLTWH(left + rectWidth, top, size.width - left - rectWidth, rectHeight), paint);

    final outlinePaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    canvas.drawRect(Rect.fromLTWH(left, top, rectWidth, rectHeight), outlinePaint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}

Future<String> cropTo800x600(String imagePath) async {
  final imageFile = File(imagePath);
  final bytes = await imageFile.readAsBytes();
  final originalImage = img.decodeImage(bytes);

  if (originalImage == null) {
    throw Exception('Failed to decode image');
  }

  final exifData = await readExifFromBytes(bytes);
  final orientationTag = exifData['Image Orientation'];
  final orientation = orientationTag?.values.firstAsInt() ?? 1;

  debugPrint('EXIF Orientation: $orientation');

  img.Image orientedImage;
  switch (orientation) {
    case 3:
      orientedImage = img.copyRotate(originalImage, angle: 180);
      break;
    case 6:
      orientedImage = img.copyRotate(originalImage, angle: 0);
      break;
    case 8:
      orientedImage = img.copyRotate(originalImage, angle: -90);
      break;
    default:
      orientedImage = originalImage;

  }

  const cropWidth = 800;
  const cropHeight = 600;
  const aspectRatio = cropWidth / cropHeight;

  int x, y, w, h;
  if (orientedImage.width / orientedImage.height > aspectRatio) {
    h = orientedImage.height;
    w = (h * aspectRatio).round();
    y = 0;
    x = ((orientedImage.width - w) / 2).round();
  } else {
    w = orientedImage.width;
    h = (w / aspectRatio).round();
    x = 0;
    y = ((orientedImage.height - h) / 2).round();
  }

  final croppedImage = img.copyCrop(orientedImage, x: x, y: y, width: w, height: h);
  final resizedImage = img.copyResize(croppedImage, width: cropWidth, height: cropHeight);

  final tempDir = await getTemporaryDirectory();
  final croppedFile = File('${tempDir.path}/cropped_image_${DateTime.now().millisecondsSinceEpoch}.jpg');
  await croppedFile.writeAsBytes(img.encodeJpg(resizedImage));
  return croppedFile.path;
}

class DisplayPictureScreen extends StatefulWidget {
  final String imagePath;

  const DisplayPictureScreen({super.key, required this.imagePath});

  @override
  State<DisplayPictureScreen> createState() => _DisplayPictureScreenState();
}

class _DisplayPictureScreenState extends State<DisplayPictureScreen> {
  bool _isLoading = false;

  Future<void> _processImage() async {
    setState(() {
      _isLoading = true;
    });

    try {
      String processedImagePath = await sendImageToServer(widget.imagePath);
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (context) => ProcessedImageScreen(imagePath: processedImagePath),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<String> sendImageToServer(String imagePath) async {
    try {
       var uri = Uri.parse('https://seal-app-8f9gu.ondigitalocean.app/predict');
      debugPrint('Sending request to: $uri');

      var request = http.MultipartRequest('POST', uri);
      request.files.add(await http.MultipartFile.fromPath('file', imagePath));

      debugPrint('Sending request...');
      var streamedResponse = await request.send().timeout(const Duration(seconds: 30));
      var response = await http.Response.fromStream(streamedResponse);

      debugPrint('Response received. Status code: ${response.statusCode}');
      debugPrint('Response headers: ${response.headers}');
      debugPrint('Response body length: ${response.bodyBytes.length}');

      if (response.statusCode == 200) {
        if (response.bodyBytes.isNotEmpty) {
          final tempDir = await getTemporaryDirectory();
          File file = File('${tempDir.path}/response_image_${DateTime.now().millisecondsSinceEpoch}.png');
          await file.writeAsBytes(response.bodyBytes);
          debugPrint('Image saved to: ${file.path}');
          return file.path;
        } else {
          throw Exception('Response body is empty');
        }
      } else {
        debugPrint('Error response body: ${response.body}');
        throw Exception('Server returned status code ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('Error in sendImageToServer: $e');
      if (e is SocketException) {
        throw Exception('Failed to connect to the server. Please check your internet connection.');
      } else if (e is TimeoutException) {
        throw Exception('Connection to server timed out. Please try again.');
      } else {
        throw Exception('Failed to send image to server: $e');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async {
        Navigator.of(context).pop();
        return false;
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Confirm Image'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.of(context).pop(),
          ),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AspectRatio(
                aspectRatio: 800 / 600,
                child: Image.file(
                  File(widget.imagePath),
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton(
                    onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
                    child: const Text('Retake', style: TextStyle(fontSize: 18)),
                  ),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _processImage,
                    child: _isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          )
                        : const Text('Confirm', style: TextStyle(fontSize: 18)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ProcessedImageScreen extends StatelessWidget {
  final String imagePath;

  const ProcessedImageScreen({super.key, required this.imagePath});

  Future<bool> requestStoragePermission() async {
    if (Platform.isAndroid) {
      if (await Permission.manageExternalStorage.request().isGranted) {
        return true;
      }
    } else if (await Permission.storage.request().isGranted) {
      return true;
    }
    return false;
  }

  Future<void> saveImage(BuildContext context) async {
    try {
      if (!(await requestStoragePermission())) {
        throw Exception('Storage permission denied');
      }

      String? selectedDirectory = await FilePicker.platform.getDirectoryPath();

      if (selectedDirectory == null) {
        throw Exception('No directory selected');
      }

      final savedImage = await File(imagePath).copy('$selectedDirectory/processed_image_${DateTime.now().millisecondsSinceEpoch}.png');

      if (!context.mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Image saved to ${savedImage.path}')),
      );
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => const TakePictureScreen()),
        (Route<dynamic> route) => false,
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to save image: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const TakePictureScreen()),
        );
        return false;
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Processed Image'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () {
              Navigator.of(context).pushReplacement(
                MaterialPageRoute(builder: (context) => const TakePictureScreen()),
              );
            },
          ),
        ),
        body: Center(
          child: SingleChildScrollView(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Image.file(
                  File(imagePath),
                  fit: BoxFit.contain,
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () => saveImage(context),
                  child: const Text('Save Image', style: TextStyle(fontSize: 18)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}