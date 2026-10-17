from flask import Flask, render_template, send_from_directory, request, send_file, redirect, url_for
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))

@app.route('/', methods=['GET', 'POST'])
def index():
    data = {
        'selected_image': 'logo.svg',
        'text_top': '',
        'text_bottom': '',
        'selected_color': 'white',
        'text_top_y': '20',
        'text_bottom_y': '20',
    }
    if request.method == 'POST':
        allowed_images = {'logo.svg', 'meme_1.jpg', 'meme_2.jpg', 'meme_3.jpg', 'meme_4.jpg', 'meme_5.jpg'}
        selected_image = request.form.get('image-selector', 'logo.svg')
        if selected_image in allowed_images:
            data['selected_image'] = selected_image
        data['text_top'] = request.form.get('text_top', '').strip()
        data['text_bottom'] = request.form.get('text_bottom', '').strip()
        color = request.form.get('color-selector', 'white')
        data['selected_color'] = color if color in {'white', 'black'} else 'white'
        for key in ('text_top_y', 'text_bottom_y'):
            try:
                data[key] = str(max(0, min(100, int(request.form.get(key, data[key])))))
            except (TypeError, ValueError):
                pass
    return render_template('index.html', **data)


@app.route('/guardar', methods=['POST'])
def guardar_meme():
    allowed_images = {'meme_1.jpg', 'meme_2.jpg', 'meme_3.jpg', 'meme_4.jpg', 'meme_5.jpg'}
    selected_image = request.form.get('image-selector', 'meme_1.jpg')
    if selected_image not in allowed_images:
        return redirect(url_for('index'))

    image_path = BASE_DIR / 'static' / 'img' / selected_image
    with Image.open(image_path) as original:
        meme = original.convert('RGB')

    draw = ImageDraw.Draw(meme)
    width, height = meme.size
    font_size = max(18, min(width // 10, 64))
    font = None
    for font_path in ('C:/Windows/Fonts/impact.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    color_choice = request.form.get('color-selector', 'white')
    fill = 'white' if color_choice == 'white' else 'black'
    outline = 'black' if fill == 'white' else 'white'

    def draw_centered_text(text, y_percent):
        text = text.strip()
        if not text:
            return
        # Ajusta el tamaño si el texto es demasiado largo para la imagen.
        local_font = font
        max_width = int(width * 0.92)
        while local_font.size > 12 and draw.textbbox((0, 0), text, font=local_font, stroke_width=2)[2] > max_width:
            local_font = ImageFont.truetype(font.path, local_font.size - 2) if getattr(local_font, 'path', None) else ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=local_font, stroke_width=2)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        y = int(height * max(0, min(100, y_percent)) / 100)
        draw.text((x, y), text, font=local_font, fill=fill, stroke_width=max(2, font_size // 16), stroke_fill=outline)

    try:
        top_y = int(request.form.get('text_top_y', '20'))
    except ValueError:
        top_y = 20
    try:
        bottom_y = int(request.form.get('text_bottom_y', '20'))
    except ValueError:
        bottom_y = 20
    top_y = max(0, min(100, top_y))
    bottom_y = max(0, min(100, bottom_y))

    draw_centered_text(request.form.get('text_top', ''), top_y)
    bottom_text = request.form.get('text_bottom', '').strip()
    if bottom_text:
        # El porcentaje inferior se mide desde el borde de abajo, igual que en la vista previa.
        bbox = draw.textbbox((0, 0), bottom_text, font=font, stroke_width=2)
        text_height = bbox[3] - bbox[1]
        y = int(height * (1 - bottom_y / 100) - text_height)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        draw.text((x, y), bottom_text, font=font, fill=fill, stroke_width=max(2, font_size // 16), stroke_fill=outline)

    output = BytesIO()
    meme.save(output, format='PNG')
    output.seek(0)
    return send_file(output, mimetype='image/png', as_attachment=True, download_name='mi-meme.png')

@app.route('/static/img/<path:path>')
def serve_images(path):
    return send_from_directory(str(BASE_DIR / 'static' / 'img'), path)

if __name__ == '__main__':
    app.run(debug=True)
