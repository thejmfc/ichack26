import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import glob
import pandas as pd
from pathlib import Path

# =====================
# Configuration
# =====================
IMAGES_DIR = "images"
RATINGS_CSV = "property_ratings.csv"
THUMBNAIL_SIZE = (600, 400)

class PropertyRatingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Property Photo Rating Tool")
        self.root.geometry("900x700")
        
        # Get all images
        self.image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.avif']:
            self.image_files.extend(glob.glob(os.path.join(IMAGES_DIR, ext)))
        self.image_files.sort()
        
        if not self.image_files:
            messagebox.showerror("Error", f"No images found in {IMAGES_DIR}")
            root.destroy()
            return
        
        # Load existing ratings if available
        self.ratings = {}
        if os.path.exists(RATINGS_CSV):
            df = pd.read_csv(RATINGS_CSV)
            self.ratings = dict(zip(df['image_path'], df['property_score']))
        
        self.current_index = 0
        self.current_photo = None
        
        # Setup UI
        self.setup_ui()
        self.load_image()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="Property Photo Rating Tool", font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Image display
        self.image_label = ttk.Label(main_frame, background="#f0f0f0")
        self.image_label.grid(row=1, column=0, columnspan=3, pady=10)
        
        # File info
        self.info_label = ttk.Label(main_frame, text="", font=("Arial", 10))
        self.info_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        # Rating info
        self.rating_label = ttk.Label(main_frame, text="Rate this property (1-10):", font=("Arial", 12))
        self.rating_label.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Label(input_frame, text="Enter rating: ", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        # Rating input
        self.rating_input = ttk.Entry(input_frame, width=5, font=("Arial", 14))
        self.rating_input.pack(side=tk.LEFT, padx=5)
        self.rating_input.bind("<Return>", lambda e: self.next_image())
        
        # Rating display
        self.rating_display = ttk.Label(main_frame, text="5", font=("Arial", 20, "bold"), 
                                        foreground="blue")
        self.rating_display.grid(row=5, column=0, columnspan=3, pady=5)
        
        # Descriptions
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=6, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        descriptions = [
            "1-3: Poor (unappealing, messy, bad lighting)",
            "4-5: Below Average (decent but not appealing)",
            "6-7: Good (nice, clean, good lighting)",
            "8-9: Excellent (very appealing, great layout)",
            "10: Perfect (ideal property interior/exterior)"
        ]
        
        for desc in descriptions:
            ttk.Label(desc_frame, text=desc, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="◀ Previous", command=self.previous_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save & Next ▶", command=self.next_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skip", command=self.skip_image).pack(side=tk.LEFT, padx=5)
        
        # Progress
        self.progress_label = ttk.Label(main_frame, text="", font=("Arial", 10))
        self.progress_label.grid(row=8, column=0, columnspan=3, pady=10)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress_bar.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=20)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="", font=("Arial", 10), foreground="green")
        self.status_label.grid(row=10, column=0, columnspan=3, pady=5)
    
    def load_image(self):
        """Load and display current image"""
        if self.current_index >= len(self.image_files):
            self.current_index = len(self.image_files) - 1
        
        image_path = self.image_files[self.current_index]
        filename = os.path.basename(image_path)
        
        # Load image
        try:
            img = Image.open(image_path)
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            self.current_photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.current_photo)
        except Exception as e:
            self.image_label.config(text=f"Error loading image: {e}")
        
        # Update info
        file_size = os.path.getsize(image_path) / 1024  # KB
        self.info_label.config(text=f"{filename} ({file_size:.1f} KB)")
        
        # Update progress
        progress = ((self.current_index + 1) / len(self.image_files)) * 100
        self.progress_bar['value'] = progress
        self.progress_label.config(text=f"Image {self.current_index + 1}/{len(self.image_files)}")
        
        # Load existing rating if available
        if image_path in self.ratings:
            rating = self.ratings[image_path]
            self.rating_input.delete(0, tk.END)
            self.rating_display.config(text=f"{rating:.1f}")
            self.status_label.config(text=f"Already rated: {rating:.1f}/10", foreground="orange")
        else:
            self.rating_input.delete(0, tk.END)
            self.rating_display.config(text="")
            self.status_label.config(text="", foreground="green")
        
        self.rating_input.focus()
    
    def on_slider_change(self, value):
        """Update rating display when slider changes"""
        rating = float(value)
        self.rating_display.config(text=f"{rating:.0f}")
    
    def save_rating(self):
        """Save current rating"""
        image_path = self.image_files[self.current_index]
        try:
            rating = float(self.rating_input.get())
            if 1 <= rating <= 10:
                self.ratings[image_path] = rating
                self.status_label.config(text=f"✓ Saved rating: {rating:.1f}/10", foreground="green")
                return True
            else:
                self.status_label.config(text="⚠ Please enter a number between 1 and 10", foreground="red")
                return False
        except ValueError:
            self.status_label.config(text="⚠ Please enter a valid number (1-10)", foreground="red")
            return False
    
    def next_image(self):
        """Save current and move to next"""
        if self.save_rating():
            # Update display
            try:
                rating = float(self.rating_input.get())
                self.rating_display.config(text=f"{rating:.1f}")
            except:
                pass
            
            self.current_index += 1
            if self.current_index < len(self.image_files):
                self.load_image()
            else:
                self.save_all_ratings()
                messagebox.showinfo("Done!", f"All {len(self.image_files)} images rated!\nRatings saved to {RATINGS_CSV}")
                self.root.destroy()
    
    def previous_image(self):
        """Move to previous image"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
    
    def skip_image(self):
        """Skip current image without rating"""
        self.current_index += 1
        if self.current_index < len(self.image_files):
            self.load_image()
        else:
            self.save_all_ratings()
            messagebox.showinfo("Done!", "Finished rating images!")
            self.root.destroy()
    
    def save_all_ratings(self):
        """Save all ratings to CSV"""
        if not self.ratings:
            return
        
        ratings_data = []
        for image_path, score in self.ratings.items():
            ratings_data.append({
                'image_path': image_path,
                'filename': os.path.basename(image_path),
                'property_score': score
            })
        
        df = pd.DataFrame(ratings_data)
        df.to_csv(RATINGS_CSV, index=False)
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"Ratings saved to {RATINGS_CSV}")
        print(f"Total images rated: {len(ratings_data)}")
        print(f"Average rating: {df['property_score'].mean():.2f}")
        print(f"Min rating: {df['property_score'].min():.1f}")
        print(f"Max rating: {df['property_score'].max():.1f}")
        print(f"{'='*70}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PropertyRatingGUI(root)
    root.mainloop()
