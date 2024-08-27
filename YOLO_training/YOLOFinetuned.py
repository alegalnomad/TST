from ultralytics import YOLO

def main():
    # Load a model
    model = YOLO("C:/Users/anand/OneDrive - The University of Nottingham/MScProject/YOLO/best.pt")  # load a pretrained model (recommended for training)

    # Use the model
    model.train(data="C:/Users/anand/OneDrive - The University of Nottingham/MScProject/YOLO/data.yaml", epochs=500)  # train the model
    metrics = model.val()  # evaluate model performance on the validation set
    #results = model("C:/Users/anand/OneDrive - The University of Nottingham/MScProject/YOLO/test/images/ISIC_0024659.jpg")  # predict on an image
    path = model.export(format="torchscript", dynamic=True) 


if __name__ == '__main__':
    main()
    pass