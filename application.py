#backend aplikace
#obsahuje infrastrukturu k navigaci mezi stránkami, zpracovává snímky od uživatele
from flask import Flask, render_template, request
import os
import base64
import re
from io import BytesIO
from PIL import ImageDraw, Image 
import sys
sys.path.append('python') #umožní importovat soubory z jiné složky
from predict import main


#následující funkce vykreslující boxy kolem detekovaných objektů
def draw_boxes(image, predictions): 
    #nejmenší validní počet nalezených objektů
    if len(predictions) <= 1: 
        return None

    img_width, img_height = image.size #předání rozměrů
    img = ImageDraw.Draw(image) 
    
    for i, obj in enumerate(predictions):
        if i > 1: break
        x0 = obj['boundingBox']['left'] * img_width  #horní levý roh
        y0 = obj['boundingBox']['top'] * img_height

        x1 = x0 + (obj['boundingBox']['width'] * img_width) #dolní pravý roh
        y1 = y0 + (obj['boundingBox']['height'] * img_height)
        shape = [(x0, y0), (x1, y1)]

        img.rectangle(shape, outline ="red") #nakreslí box
        img.text((x0 + 10, y0 + 10), obj['tagName'], fill="red") #přidá popisek

    return image


app = Flask(__name__) #vytvoření instance aplikace
app.config['IMAGE_UPLOADS'] = 'static/img/user_img' #složka se snímky uživatelů


@app.route("/") #základní menu
def home():
    #vymaže nahrané snímky od předchozích uživatelů
    for file in os.listdir(app.config['IMAGE_UPLOADS']): 

        file_path = os.path.join(app.config['IMAGE_UPLOADS'], file)

        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

        except Exception as e:


            print('Failed to delete %s. Reason: %s' % (file_path, e))
    
    return render_template('index.html')


@app.route("/camera", methods=['GET', 'POST']) #pořizování snímků
def camera():
    return render_template('camera.html', message="pokuď kameru nevidíte musíte ji buď zapnout nebo povolit v prohlížeči")
    

@app.route("/detect", methods=['GET', 'POST']) #zobrazení výsledků
def detection():
    
    if request.method == 'POST':

            image_b64 = request.values['image'] #vyžádání obrázku z html form jako base64 data
            image_b64 = re.sub('^data:image/.+;base64,', '', image_b64) #odříznutí metadat
            image_data = BytesIO(base64.b64decode(image_b64)) #dekódovaní base64 dat
            image = Image.open(image_data)

            predictions = main(image_data) #předání snímku customvision modelu
            image = draw_boxes(image, predictions) #vykreslí boxy
            #pokud nenajde dost nebo žádný objekt vrátí uživatele zpět
            if image == None: return render_template('camera.html', message="Nenalezeno dost objektů, zkuste to prosím znovu.")
            #uloží snímek s vykreslenými boxy
            image = image.save(os.path.join(app.config['IMAGE_UPLOADS'], '{}.png'.format(predictions[0]['probability']))) 

            return render_template('choice.html', user_image=os.path.join(app.config['IMAGE_UPLOADS'], '{}.png'.format(predictions[0]['probability']))
            ,port1=predictions[0]['tagName'], port2=predictions[1]['tagName'])


if __name__ == "__main__":
        app.run(host='0.0.0.0',port="8000",debug=True)
