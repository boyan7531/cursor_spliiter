from moviepy.editor import VideoFileClip, CompositeVideoClip, clips_array, ColorClip, concatenate_videoclips, TextClip
import numpy as np
import os
from moviepy.config import change_settings
import speech_recognition as sr
import tempfile
import math

# Configure ImageMagick path
IMAGEMAGICK_BINARY = os.path.join(r"C:\Program Files\ImageMagick-7.1.1-Q16", "magick.exe")
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})

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
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
    def extract_audio_segment(self, start_time, end_time):
        """Extract audio segment from gameplay video and save it temporarily"""
        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        audio_segment = self.gameplay.subclip(start_time, end_time).audio
        audio_segment.write_audiofile(temp_audio_file.name, fps=16000)
        return temp_audio_file.name
        
    def generate_subtitles(self, start_time, end_time):
        """Generate subtitles using speech recognition for the specified time segment"""
        # Extract audio segment
        audio_file = self.extract_audio_segment(start_time, end_time)
        
        # Split into 10-second segments for better recognition
        clip_duration = end_time - start_time
        segment_duration = 10  # seconds
        num_segments = math.ceil(clip_duration / segment_duration)
        
        subtitle_clips = []
        
        try:
            for i in range(num_segments):
                segment_start = i * segment_duration
                segment_end = min((i + 1) * segment_duration, clip_duration)
                
                # Extract segment audio
                segment_audio_file = self.extract_audio_segment(start_time + segment_start, start_time + segment_end)
                
                # Recognize speech
                with sr.AudioFile(segment_audio_file) as source:
                    audio = self.recognizer.record(source)
                    try:
                        text = self.recognizer.recognize_google(audio)
                        if text:
                            # Create text clip for this segment
                            txt_clip = TextClip(
                                text,
                                font='Arial',
                                fontsize=40,
                                color='white',
                                size=(self.target_width * 1.2, None),
                                method='caption'
                    
                            ).set_duration(segment_end - segment_start)
                            
                            # Adjust timing relative to video start
                            txt_clip = txt_clip.set_start(segment_start)
                            subtitle_clips.append(txt_clip)
                    except sr.UnknownValueError:
                        print(f"Could not understand audio in segment {i+1}")
                    except sr.RequestError as e:
                        print(f"Could not request results in segment {i+1}; {e}")
                
                # Clean up segment audio file
                os.unlink(segment_audio_file)
        
        finally:
            # Clean up main audio file
            os.unlink(audio_file)
        
        return subtitle_clips
        
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
        
        # Generate subtitles
        subtitle_clips = self.generate_subtitles(start_time, end_time)
        
        # Position all subtitle clips
        subtitle_y = gameplay_y + gameplay_height - 30  # Overlap with bottom of gameplay
        positioned_subtitles = []
        for sub_clip in subtitle_clips:
            sub_w = sub_clip.w if hasattr(sub_clip, 'w') else self.target_width * 0.9
            subtitle_x = (self.target_width - sub_w) / 2
            positioned_sub = sub_clip.set_position((subtitle_x, subtitle_y))
            positioned_subtitles.append(positioned_sub)
        
        # Create black background
        background = ColorClip(size=(self.target_width, self.target_height), 
                             color=(0, 0, 0),
                             duration=end_time - start_time)
        
        # Set the duration for both clips explicitly
        gameplay_positioned = gameplay_resized.set_position((gameplay_x, gameplay_y)).set_duration(end_time - start_time)
        attention_positioned = attention_resized.set_position((attention_x, attention_y)).set_duration(end_time - start_time)
        
        # Create final composition with background
        clips_to_compose = [background, gameplay_positioned, attention_positioned] + positioned_subtitles
        final_video = CompositeVideoClip(
            clips_to_compose,
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