
def highlight(arr, x, y):
    from PIL import Image
    # sample a pixel position and use a combinatorial 'inversion'
    # of the color value, so it's always visible.
    img = Image.fromarray(arr, "RGB")
    pix = img.load()
    R, G, B = pix[x, y]
    return (R + 128) % 255, (G + 128) % 255, (B + 128) % 255
