from moviepy.editor import VideoFileClip, CompositeVideoClip, clips_array, ColorClip
import numpy as np

class VideoProcessor:
    def __init__(self, gameplay_path, attention_path):
        # Load the videos
        self.gameplay = VideoFileClip(gameplay_path)
        self.attention = VideoFileClip(attention_path)
        
        # Target dimensions for TikTok (1080x1920)
        self.target_width = 1080
        self.target_height = 1920
        
        # Scale factors (1.2 for gameplay, 1.4 for attention video)
        self.gameplay_scale = 1.2
        self.attention_scale = 1.4
        
    def process_videos(self, start_time=0, end_time=None):
        if end_time is None:
            end_time = self.gameplay.duration

        # Get subclips for the specified time range
        gameplay_clip = self.gameplay.subclip(start_time, end_time)
        
        # Create a new attention clip that matches the gameplay duration
        attention_duration = end_time - start_time
        attention_clip = self.attention.subclip(0, attention_duration)
            
        # Resize gameplay video (scaled up and positioned slightly above center)
        gameplay_resized = gameplay_clip.resize(width=self.target_width * self.gameplay_scale)
        gameplay_height = gameplay_resized.h
        gameplay_y = (self.target_height * 0.4) - (gameplay_height / 2)
        
        # Resize attention video (scaled up more and positioned below)
        attention_resized = attention_clip.resize(width=self.target_width * self.attention_scale)
        attention_resized = attention_resized.without_audio()  # Mute second video
        attention_height = attention_resized.h
        attention_y = gameplay_y + gameplay_height + 20  # 20px gap
        
        # Center videos horizontally
        gameplay_x = -(gameplay_resized.w - self.target_width) / 2
        attention_x = -(attention_resized.w - self.target_width) / 2
        
        # Create black background
        background = ColorClip(size=(self.target_width, self.target_height), 
                             color=(0, 0, 0),
                             duration=end_time - start_time)
        
        # Set the duration for both clips explicitly
        gameplay_positioned = gameplay_resized.set_position((gameplay_x, gameplay_y)).set_duration(end_time - start_time)
        attention_positioned = attention_resized.set_position((attention_x, attention_y)).set_duration(end_time - start_time)
        
        # Create final composition with background
        final_video = CompositeVideoClip(
            [background, gameplay_positioned, attention_positioned],
            size=(self.target_width, self.target_height)
        ).set_duration(end_time - start_time)
        
        return final_video
    
    def split_by_duration(self, duration_per_part):
        """Split video into parts of specified duration"""
        total_duration = min(self.gameplay.duration, self.attention.duration)
        parts = []
        
        current_time = 0
        while current_time < total_duration:
            end_time = min(current_time + duration_per_part, total_duration)
            part = self.process_videos(current_time, end_time)
            parts.append(part)
            current_time = end_time
            
        return parts
    
    def split_by_parts(self, num_parts):
        """Split video into specified number of parts"""
        total_duration = min(self.gameplay.duration, self.attention.duration)
        duration_per_part = total_duration / num_parts
        return self.split_by_duration(duration_per_part) 