import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from video_processor import VideoProcessor
import os

class VideoProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Processor")
        self.root.geometry("600x400")
        
        self.gameplay_path = None
        self.attention_path = None
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection buttons
        ttk.Button(self.main_frame, text="Select Gameplay Video", command=self.select_gameplay).grid(row=0, column=0, pady=5)
        self.gameplay_label = ttk.Label(self.main_frame, text="No file selected")
        self.gameplay_label.grid(row=0, column=1, pady=5)
        
        ttk.Button(self.main_frame, text="Select Attention Video", command=self.select_attention).grid(row=1, column=0, pady=5)
        self.attention_label = ttk.Label(self.main_frame, text="No file selected")
        self.attention_label.grid(row=1, column=1, pady=5)
        
        # Splitting options
        ttk.Label(self.main_frame, text="Split Options:").grid(row=2, column=0, pady=10)
        self.split_var = tk.StringVar(value="none")
        
        ttk.Radiobutton(self.main_frame, text="No splitting", variable=self.split_var, 
                       value="none").grid(row=3, column=0)
        
        ttk.Radiobutton(self.main_frame, text="Split by duration (seconds)", variable=self.split_var, 
                       value="duration").grid(row=4, column=0)
        self.duration_entry = ttk.Entry(self.main_frame)
        self.duration_entry.grid(row=4, column=1)
        
        ttk.Radiobutton(self.main_frame, text="Split by number of parts", variable=self.split_var, 
                       value="parts").grid(row=5, column=0)
        self.parts_entry = ttk.Entry(self.main_frame)
        self.parts_entry.grid(row=5, column=1)
        
        # Process button
        ttk.Button(self.main_frame, text="Process Videos", command=self.process_videos).grid(row=6, column=0, columnspan=2, pady=20)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=7, column=0, columnspan=2)

    def select_gameplay(self):
        self.gameplay_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if self.gameplay_path:
            self.gameplay_label.config(text=os.path.basename(self.gameplay_path))

    def select_attention(self):
        self.attention_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if self.attention_path:
            self.attention_label.config(text=os.path.basename(self.attention_path))

    def process_videos(self):
        if not self.gameplay_path or not self.attention_path:
            self.status_label.config(text="Please select both videos first!")
            return
        
        try:
            processor = VideoProcessor(self.gameplay_path, self.attention_path)
            split_option = self.split_var.get()
            
            # Create output directory if it doesn't exist
            output_dir = "output_videos"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            if split_option == "none":
                self.status_label.config(text="Processing video...")
                self.root.update()
                final_video = processor.process_videos()
                output_path = os.path.join(output_dir, "output.mp4")
                final_video.write_videofile(output_path)
                self.status_label.config(text=f"Video saved to {output_path}")
                
            elif split_option == "duration":
                try:
                    duration = float(self.duration_entry.get())
                    if duration <= 0:
                        raise ValueError("Duration must be positive")
                    
                    self.status_label.config(text="Processing videos...")
                    self.root.update()
                    parts = processor.split_by_duration(duration)
                    
                    for i, part in enumerate(parts, 1):
                        self.status_label.config(text=f"Processing part {i} of {len(parts)}...")
                        self.root.update()
                        output_path = os.path.join(output_dir, f"output_part_{i}.mp4")
                        part.write_videofile(output_path)
                    
                    self.status_label.config(text=f"Created {len(parts)} videos in {output_dir}")
                    messagebox.showinfo("Success", f"Created {len(parts)} videos in {output_dir}")
                    
                except ValueError as e:
                    self.status_label.config(text="Please enter a valid positive duration!")
                    
            elif split_option == "parts":
                try:
                    num_parts = int(self.parts_entry.get())
                    if num_parts <= 0:
                        raise ValueError("Number of parts must be positive")
                    
                    self.status_label.config(text="Processing videos...")
                    self.root.update()
                    parts = processor.split_by_parts(num_parts)
                    
                    for i, part in enumerate(parts, 1):
                        self.status_label.config(text=f"Processing part {i} of {num_parts}...")
                        self.root.update()
                        output_path = os.path.join(output_dir, f"output_part_{i}.mp4")
                        part.write_videofile(output_path)
                    
                    self.status_label.config(text=f"Created {num_parts} videos in {output_dir}")
                    messagebox.showinfo("Success", f"Created {num_parts} videos in {output_dir}")
                    
                except ValueError:
                    self.status_label.config(text="Please enter a valid positive number of parts!")
                    
        except Exception as e:
            error_msg = str(e)
            self.status_label.config(text=f"Error: {error_msg}")
            messagebox.showerror("Error", error_msg)

def main():
    root = tk.Tk()
    app = VideoProcessorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 