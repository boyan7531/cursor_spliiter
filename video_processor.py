from moviepy.editor import VideoFileClip, CompositeVideoClip, clips_array, ColorClip, concatenate_videoclips
import numpy as np

class VideoProcessor:
    def __init__(self, gameplay_path, attention_path):
        # Load the videos
        self.gameplay = VideoFileClip(gameplay_path)
        self.attention = VideoFileClip(attention_path)
        
        # Target dimensions for TikTok (1080x1920)
        self.target_width = 1080
        self.target_height = 1920
        
        # Scale factors (1.2 for gameplay, 1.8 for attention video)
        self.gameplay_scale = 1.2
        self.attention_scale = 1.8
        
    def process_videos(self, start_time=0, end_time=None):
        if end_time is None:
            end_time = self.gameplay.duration

        # Get gameplay subclip
        gameplay_clip = self.gameplay.subclip(start_time, end_time)
        
        # Calculate how many times we need to loop the attention video
        clip_duration = end_time - start_time
        attention_full_duration = self.attention.duration
        loops_needed = int(np.ceil(clip_duration / attention_full_duration))
        
        # Create a list to store the attention video segments
        attention_segments = []
        remaining_duration = clip_duration
        current_time = 0
        
        # Create the looped attention video
        while remaining_duration > 0:
            segment_duration = min(remaining_duration, attention_full_duration)
            segment = self.attention.subclip(0, segment_duration)
            attention_segments.append(segment)
            remaining_duration -= segment_duration
            current_time += segment_duration
        
        # Concatenate all attention segments
        attention_clip = concatenate_videoclips(attention_segments)
            
        # Resize gameplay video (scaled up and positioned higher)
        gameplay_resized = gameplay_clip.resize(width=self.target_width * self.gameplay_scale)
        gameplay_height = gameplay_resized.h
        gameplay_y = (self.target_height * 0.3) - (gameplay_height / 2)
        
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
        total_duration = self.gameplay.duration  # Use gameplay duration as the total
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
        total_duration = self.gameplay.duration  # Use gameplay duration as the total
        duration_per_part = total_duration / num_parts
        return self.split_by_duration(duration_per_part) 