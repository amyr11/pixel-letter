import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import io  # Required for handling image bytes for download

# --- Configuration ---
DEFAULT_FONT_FILENAME = "C&C Red Alert [INET].ttf"
DEFAULT_FONT_SIZE = 30
DEFAULT_TEXT_COLOR = (0, 0, 0, 255)  # Black, fully opaque
DEFAULT_BG_COLOR = (0, 0, 0, 0)  # Transparent background


# --- Core Pixel Text Generation Function (Modified to return Image object) ---
def text_to_true_pixel_art(
    text,
    font_path,
    font_size=DEFAULT_FONT_SIZE,
    text_color=DEFAULT_TEXT_COLOR,
    bg_color=DEFAULT_BG_COLOR,
):
    """
    Generates a true pixel art image of text, mapping font pixels 1:1.

    Args:
        text (str): The text to render.
        font_path (str): The path to the TTF font file.
        font_size (int): The target point size for the font.
        text_color (tuple): The RGBA color for the text pixels.
        bg_color (tuple): The RGBA color for the background.

    Returns:
        PIL.Image.Image or None: The generated image object, or None if error.
    """
    # --- Font Loading ---
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        st.error(
            f"Error: Font file not found at '{font_path}'. "
            f"Make sure '{os.path.basename(font_path)}' is in the same directory as the script."
        )
        return None  # Return None on font error

    # --- Determine Text Dimensions ---
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    try:
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
    except AttributeError:
        # Fallback for older Pillow versions
        st.warning(
            "Using fallback for text dimension calculation (older Pillow?). Layout might be less precise."
        )
        try:
            # textlength might not exist in very new versions, but textbbox should
            text_width = int(dummy_draw.textlength(text, font=font))
            ascent, descent = font.getmetrics()
            text_height = ascent + descent
            bbox = (0, 0, text_width, text_height)
        except AttributeError:
            st.error("Cannot determine text dimensions with this Pillow version.")
            return None

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    if text_width <= 0 or text_height <= 0:
        st.warning(
            f"Text '{text}' rendered with zero width or height. Generating 1x1 empty image."
        )
        # Return a minimal transparent image
        return Image.new("RGBA", (1, 1), bg_color)

    # --- Create Final Image and Draw Text ---
    img = Image.new("RGBA", (text_width, text_height), bg_color)
    draw = ImageDraw.Draw(img)
    draw.text((-bbox[0], -bbox[1]), text, font=font, fill=text_color)

    # --- Ensure Pure Pixels (Optional but good practice for this style) ---
    img_data = img.getdata()
    new_data = []
    for item in img_data:
        if item[3] > 0:  # If alpha > 0 (pixel has color)
            new_data.append(text_color)
        else:  # Otherwise, use background color
            new_data.append(bg_color)
    img.putdata(new_data)

    return img


# --- Streamlit App UI ---

st.set_page_config(page_title="Pixel Text Generator", layout="centered")

st.title("👾 Pixel Text Generator 👾")
st.write(
    f"Create true pixel-style text using the '{DEFAULT_FONT_FILENAME}' font (at {DEFAULT_FONT_SIZE}pt)."
)

# --- Font Check ---
# Construct the absolute path to the font file relative to the script
script_dir = os.path.dirname(__file__)
font_file_path = os.path.join(script_dir, DEFAULT_FONT_FILENAME)

if not os.path.exists(font_file_path):
    st.error(f"**Font file '{DEFAULT_FONT_FILENAME}' not found!**")
    st.write(
        f"Please download the font (e.g., from DaFont) and place it "
        f"in the same directory as this Streamlit script (`{script_dir}`)."
    )
    st.stop()  # Stop execution if font is missing

# --- User Input ---
text_input = st.text_input("Enter text:", value="Hello Pixel World!")

# --- Advanced Options (Optional) ---
# with st.expander("Advanced Options"):
#     selected_color = st.color_picker("Text Color", value='#000000') # Hex for black
#     # Convert hex to RGBA tuple (assuming full opacity)
#     # This part can be enhanced for alpha selection if needed
#     r = int(selected_color[1:3], 16)
#     g = int(selected_color[3:5], 16)
#     b = int(selected_color[5:7], 16)
#     text_color_input = (r, g, b, 255)
# else:
#     text_color_input = DEFAULT_TEXT_COLOR # Use default if expander closed or not used

text_color_input = DEFAULT_TEXT_COLOR  # Keeping it simple for now

# --- Generate and Display ---
if text_input:
    # Generate the image
    pixel_image = text_to_true_pixel_art(
        text=text_input,
        font_path=font_file_path,
        font_size=DEFAULT_FONT_SIZE,
        text_color=text_color_input,
        bg_color=DEFAULT_BG_COLOR,
    )

    if pixel_image:
        st.write("---")
        st.subheader("Generated Pixel Text:")

        # Display the image - use nearest neighbor for sharp pixels when scaled by browser
        st.image(
            pixel_image,
            caption=f"'{text_input}' ({pixel_image.width}x{pixel_image.height} pixels)",
            use_container_width="auto",
            output_format="PNG",
        )  # output_format helps ensure PNG display

        st.write("---")
        st.subheader("Download")

        # Prepare image for download
        # Save image to a bytes buffer
        buf = io.BytesIO()
        pixel_image.save(buf, format="PNG")
        byte_im = buf.getvalue()

        # Create download button
        # Sanitize filename slightly (replace spaces, limit length)
        safe_filename = "".join(
            c if c.isalnum() else "_" for c in text_input[:20]
        ).rstrip("_")
        if not safe_filename:
            safe_filename = "pixel_text"  # Fallback filename

        st.download_button(
            label="Download Image (.png)",
            data=byte_im,
            file_name=f"{safe_filename}.png",
            mime="image/png",
        )
    else:
        # Error messages are handled within the function using st.error
        pass
else:
    st.info("Enter some text above to generate the pixel art.")

st.markdown("---")
st.caption("Uses Pillow library and requires a pixel font like 04B_08__.TTF.")
