import ffmpeg
import os
import subprocess
import gradio as gr

def convert_video_to_avi(input_path, output_path):
    (
        ffmpeg
        .input(input_path)
        .output(output_path, vcodec='libxvid', qscale='1', g='1000', qmin='1', qmax='1', flags='qpel+mv4', an=None)
        .overwrite_output()
        .run()
    )

def extract_frames(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    (
        ffmpeg
        .input(input_path)
        .output(f'{output_dir}/f_%05d.raw', vcodec='copy', start_number=0)
        .run()
    )

def extract_iframes(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    (
        ffmpeg
        .input(input_path)
        .filter('select', 'eq(pict_type,PICT_TYPE_I)')
        .output(f'{output_dir}/i_%05d.jpg', vsync=0, format='image2', start_number=0, frame_pts=True)
        .run()
    )
    for filename in sorted(os.listdir(output_dir)):
        if filename.endswith(".jpg"):
            image_paths.append(os.path.join(output_dir, filename))
    return image_paths

def datamoshing():

    frames_dir = "frames"

    # Create empty AVI file
    datamoshed_video_path = "datamoshed_video.avi"
    with open("datamoshed_video.avi", "wb") as f:
        pass

    # Concatenate raw frames
    for frame_file in sorted(os.listdir(frames_dir)):
        if frame_file.endswith(".raw"):
            with open(datamoshed_video_path, "ab") as f, open(os.path.join(frames_dir, frame_file), "rb") as frame:
                f.write(frame.read())
    convert_to_mp4(datamoshed_video_path)
    return "datamoshed_video.mp4"

def convert_to_mp4(input_path):
    output_path = "datamoshed_video.mp4"
    (
    ffmpeg
    .input(input_path)
    .output(output_path, vcodec='libx264')
    .overwrite_output()
    .run()
    )

def datamosh_prep(input_video):

    clean_workspace()

    avi_video_path = "input_video.avi"
    frames_dir = "frames"
    iframes_dir = "iframes"

    # Convert to AVI
    convert_video_to_avi(input_video, avi_video_path)

    # Extract frames
    extract_frames(avi_video_path, frames_dir)

    # Extract I-Frames and get their paths
    iframe_image_paths = extract_iframes(avi_video_path, iframes_dir)
    return iframe_image_paths


def get_select_index(evt: gr.SelectData):
    return evt.index

def get_selected_image(evt: gr.SelectData):
    selected_image_name = evt.value[0].split("\\")[-1]
    print(selected_image_name)
    return selected_image_name

def delete_iframe(file_name, log_message):
    os.remove(f"iframes/{file_name}")
    os.remove(f"frames/f_{file_name.split('_')[1].split('.')[0]}.raw")
    return f"{log_message}\nDeleted iframes/{file_name}"

def clean_workspace():
    for file in os.listdir("iframes"):
        os.remove(f"iframes/{file}")
    for file in os.listdir("frames"):
        os.remove(f"frames/{file}")
    for file in os.listdir("."):
        if file.endswith(".avi") or file.endswith(".mp4"):
            os.remove(file)

with gr.Blocks() as blocks:

    clean_workspace()

    # Create components
    input_video = gr.Video(label="Upload Video")
    submit_button = gr.Button("Extract I-Frames")
    iframe_gallery = gr.Gallery(label="I-Frame Images", preview=True)
    submit_button.click(datamosh_prep, inputs=[input_video], outputs=[iframe_gallery])
    
    selected = gr.Number(show_label=False)
    iframe_gallery.select(get_select_index, None, selected)

    selected_image = gr.Textbox(show_label=False)
    iframe_gallery.select(get_selected_image, None, selected_image)

    delete_iframes_button = gr.Button("Delete I-Frames")
    log = gr.Textbox(label="Log")
    delete_iframes_button.click(delete_iframe, inputs=[selected_image, log], outputs=[log])
    datamosh_button = gr.Button("Datamosh")
    datamoshed_video = gr.Video(label="Datamoshed Video")
    datamosh_button.click(datamoshing, outputs=[datamoshed_video])

blocks.launch()