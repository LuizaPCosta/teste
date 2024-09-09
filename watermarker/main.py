from tkinter import *
from tkinter import ttk
from tkinter import colorchooser
from tkinter import filedialog
from PIL import ImageTk, Image, ImageOps, ImageDraw, ImageFont
from matplotlib import font_manager

# constants:
ROOT_WIDTH = 1100
ROOT_HEIGHT = 800
MAIN_COLOR = "#B1C5CA"
BUTTON_COLOR = "#9FB1B5"

root = Tk()
root.minsize(width=ROOT_WIDTH, height=ROOT_HEIGHT)
root.title("Watermarker")
root.config(bg=MAIN_COLOR)

font_list = []
font_files = font_manager.findSystemFonts(fontpaths=None, fontext='ttf') 
for file in font_files:
    font_list.append(file.split('/')[-1].split(".")[0])


# -------------------- image functions ----------------------------------
def image_chooser():
    global image
    filename = filedialog.askopenfilename()   
    image = filename

    resize_image(image)


def resize_image(image):
    global resized_img
    img = Image.open(image)
    size = (int((ROOT_WIDTH/2)-20), int(ROOT_HEIGHT-20))   
    resized_img = ImageOps.contain(img, size)  # fits the image in the given frame size
    
    show_image(resized_img)


def show_image(resized_img):
    img_view = ImageTk.PhotoImage(resized_img)
    label.configure(image=img_view)
    label.image=img_view

# --------------------- Watermark functions ----------------------------

def choice_wm():

    global wm_button

    choice = type_wm.get()

    if choice == "Upload watermark":  # creates a button to choose the file
        try: # removes widgets from screen if the option to type watermark had been selected before
            wm_entry.place_forget()
            font_label.place_forget()
            font_options.place_forget()
            font_size_label.place_forget()
            font_size_options.place_forget()
            font_color_label.place_forget()
            color_button.place_forget()
            position_label.place_forget()
            position_options.place_forget()
        except:                                   
            pass
        wm_button = Button(text="Upload Watermark", command=wm_chooser, width=25, bg=BUTTON_COLOR, highlightthickness=0)
        wm_button.place(x=40, y=300) #!!!!
      


    else:  # creates an entry to type the watermark text
        try:
            wm_button.place_forget()
        except:                                   
            pass
        create_watermark_text()
        font_label.place(x=50, y=400)
        font_options.place(x=100, y=400)
        font_size_label.place(x=300, y=400)
        font_size_options.place(x=350, y=400)
        font_color_label.place(x=100, y=500)
        color_button.place(x=200, y=500)
        position_label.place(x=300, y=500)
        position_options.place(x=500, y=500)

def create_watermark_text():
    global wm_entry
    global wm_text 
    wm_text_label = Label(text="Type your watermark here", background=MAIN_COLOR)
    wm_text_label.place(x=40, y=300)
    wm_text = StringVar()
    wm_entry = ttk.Entry(root, textvariable=wm_text, width=30)
    wm_entry.bind('<KeyRelease>', lambda value: place_wm_text())  # will recieve every key typed  #!!
    wm_entry.place(x=250, y=300)
        

# ---------------------------- chosen watermark ------------------------       

def wm_chooser():
    filewmname = filedialog.askopenfilename()
    resize_wm(filewmname)


def resize_wm(filewmname):
    global resized_wm
    img = Image.open(filewmname)
    resized_wm = img.resize((100,100))  
    paste_wm_file()


def paste_wm_file():
    photo = resized_img
    watermark = resized_wm
    try:
        photo.paste(watermark, ((photo.size[0]-100),(photo.size[1]-100)), mask=watermark) # if it has a transparent background
    except:
        photo.paste(watermark, ((photo.size[0]-100),(photo.size[1]-100)))   # colocar a opção de remover marca d'água??
    marked_photo = ImageTk.PhotoImage(photo)                                
    label.configure(image=marked_photo)
    label.image = marked_photo

# --------------------------- written watermark --------------------------

def place_wm_text():  # show it on the image
    global text_font
    resize_image(image)  # refresh it every time so the text can be deleted in real time
    writing = ImageDraw.Draw(resized_img) 
    try:
        text_size = int(chosen_font_size.get())
    except:
        text_size = 30
    try:
        text_font = ImageFont.truetype(chosen_font.get()+'.ttf', text_size) 
    except:
        text_font = ImageFont.truetype('Ubuntu-M.ttf', text_size) 
    try:
        text_color = chosen_text_color[1]
    except:
        text_color = (255, 255, 255, 0) 
    try:
        text_position = the_position
    except:
        text_position = ((resized_img.size[0]-(get_text_metrics(text_font)[0]+25)),(resized_img.size[1]-(get_text_metrics(text_font)[1]+25)))
    
    writing.text(xy=text_position,text=wm_text.get(), fill=text_color, font=text_font)    
    written_photo = ImageTk.PhotoImage(resized_img)
    label.configure(image=written_photo)
    label.image = written_photo

def font_color():
    global chosen_text_color
    chosen_text_color = colorchooser.askcolor(initialcolor="#ffffff")
    color_button.config(background=chosen_text_color[1])
    place_wm_text()

def position_watermark():
    global the_position
    position = chosen_position.get()
    right = (resized_img.size[0]-(get_text_metrics(text_font)[0]+15))
    left = 15
    center_width = ((resized_img.size[0]/2)-(get_text_metrics(text_font)[0])/2)
    center_height = (resized_img.size[1]/2-(get_text_metrics(text_font)[1]/2))
    bottom = (resized_img.size[1]-(get_text_metrics(text_font)[1]+15))
    top = 15
    position_dictionary = {
        "Bottom Right": (right, bottom),
        "Bottom Left": (left, bottom), 
        "Bottom Center": (center_width, bottom),
        "Center": (center_width, center_height),
        "Middle Right": (right, center_height),
        "Middle Left": (left, center_height),
        "Top center": (center_width, top),
        "Top Right": (right, top),
        "Top Left": (left, top)
    }
    the_position = position_dictionary[position]
    place_wm_text()

   
def get_text_metrics(text_font):
    try:
        ascent, descent = text_font.getmetrics()

        text_width = text_font.getmask(wm_text.get()).getbbox()[2]
        text_height = text_font.getmask(wm_text.get()).getbbox()[3] + descent
        return(text_width, text_height)
    except:
        return(0,0) # Otherwise it will return an error if the text entry is empty
     

# -------------------------------------------------------------------------

# Upload Image Frame
upload_frame = LabelFrame(root, text="Upload Image", width=500, height=150, background="#B1C5CA")
upload_frame.place(x=30, y=30)

# Upload Image Button
image_button = Button(text="Upload image", command=image_chooser, width=50, bg="#9FB1B5", highlightthickness=0) 
image_button.place(x=70, y=55)

upload_wm_frame = LabelFrame(root, text="Watermark", width=500, height=550, background="#B1C5CA")
upload_wm_frame.place(x=30, y=200)

wm_label = Label(text="Choose how to add Watermark", background="#B1C5CA")
wm_label.place(x=40, y=250)

type_wm = StringVar()
type_wm_cbx = ttk.Combobox(root, textvariable=type_wm, values=("Upload watermark", "Create text watermark"))
type_wm_cbx.bind('<<ComboboxSelected>>', lambda value: choice_wm())
type_wm_cbx.place(x=260, y=250)

test_image = ImageTk.PhotoImage(Image.new('RGB',(550, 800),'rgb(237,241,249)'))  # ('RGB',(size, size),'rgb(code,code,code)')
label = Label(root, image=test_image, height=800, width=550, background="#EDF1F9")
label.place(x=550, y=0)

# choose font of the watermark
font_label = Label(text="Font: ")
chosen_font = StringVar()
font_options = ttk.Combobox(root, textvariable=chosen_font, values=font_list)
font_options.bind('<<ComboboxSelected>>', lambda value: place_wm_text())

# choose size of the watermark
font_size_label = Label(text="Size: ")
chosen_font_size = StringVar()
font_size_options = ttk.Combobox(root, textvariable=chosen_font_size, values=[10 ,15, 20, 25, 30, 35, 40, 45, 50, 55, 60])
font_size_options.bind('<<ComboboxSelected>>', lambda value: place_wm_text())

# choose color of the watermark
font_color_label = Label(text="Color: ")
color_button = Button(text="", background="#ffffff", command=font_color)

# choose watermark position
position_label = Label(text="Position: ")
chosen_position = StringVar()
position_options = ttk.Combobox(root, textvariable=chosen_position, values=["Center", "Bottom Left", "Bottom Right", "Bottom Center", "Middle Right", "Middle Left", "Top center", "Top Right", "Top Left"])
position_options.bind('<<ComboboxSelected>>', lambda value: position_watermark())




root.mainloop()

# bugs to be correted:
# don't let choose anything that is not .jpeg, .jpg, .png, .gif in image and in watermark
# don't let choose watermark before choosing the image
# substituir marca d'água se já tiver uma lá 
# lembrar a posição quando troca a fonte ou o tamanho ou o texto!

# color palette: https://color.adobe.com/pt/search?q=tech
