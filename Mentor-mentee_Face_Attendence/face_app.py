import cv2 # type: ignore
import face_recognition # type: ignore
import mediapipe as mp # type: ignore
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk # type: ignore
import threading
import os
import csv
import subprocess
import sys

with open("Requirements.txt", "r") as f:
    packages = [line.strip() for line in f if line.strip()]

for package in packages:
    try:
        __import__(package.replace("-", "_"))  
        print(f"{package} is already installed ")
    except ImportError:
        print(f"{package} not found. Installing... ")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=5, refine_landmarks=True)

def load_info_from_file(file_path="info.txt"):
    known_names = []
    subordinates = {}
    
    current_boss = None
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            
            if line[0].isdigit() and "." in line:
                
                boss_name = line.split(".", 1)[1].strip()
                known_names.append(boss_name)
                subordinates[boss_name] = []
                current_boss = boss_name

            
            elif current_boss and (line[0].isalpha() or line[0] in "-."):
                
                sub_name = line.split(".", 1)[1].strip()
                subordinates[current_boss].append(sub_name)

    return known_names, subordinates



known_names, subordinates = load_info_from_file("info.txt")

#print("Known Names:", known_names)
#print("Subordinates:", subordinates)


known_faces = []
for name in known_names:
    face_path = os.path.join("faces", f"{name}.jpg")
    try:
        img = face_recognition.load_image_file(face_path)
        encodings = face_recognition.face_encodings(img)
        if encodings:
            known_faces.append(encodings[0])
        else:
            print(f"No face found in {face_path}")
            known_faces.append(None)
    except FileNotFoundError:
        print(f"File not found: {face_path}")
        known_faces.append(None)



dps_photos = {}
for name in known_names:
    dps_path = os.path.join("DisplayPicture", f"{name}.jpg")
    if os.path.exists(dps_path):
        try:
            img = Image.open(dps_path).resize((120, 120))
            dps_photos[name] = img  
        except Exception as e:
            print(f"Error loading DPS for {name}: {e}")
    else:
        print(f"DPS photo not found for {name}")




def show_attendance_window(boss_name, icon_path="required_images/Logo.jpg"):
    root = tk.Tk()
    root.title(f"{boss_name}'s Team Attendance")
    root.geometry("850x650")

    if os.path.exists("required_images/Background_Image.jpg"):
        bg_img = Image.open("required_images/Background_Image.jpg").resize((850, 650))
        bg_photo = ImageTk.PhotoImage(bg_img)

        bg_label = tk.Label(root, image=bg_photo)
        bg_label.image = bg_photo  
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    

    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path).resize((32, 32))
        root.icon_photo = ImageTk.PhotoImage(icon_img)
        root.iconphoto(True, root.icon_photo)

    header_frame = tk.Frame(root, bg="black")
    header_frame.pack(pady=15, fill="x")

    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path).resize((80, 100))
        icon_photo = ImageTk.PhotoImage(icon_img)
        icon_label = tk.Label(header_frame, image=icon_photo, bg="black",
                              bd=2, relief="solid", highlightbackground="green", highlightthickness=2)
        icon_label.image = icon_photo
        icon_label.pack(side="left", padx=20)

    if boss_name in dps_photos:
        boss_img = dps_photos[boss_name].resize((160, 160))   
        boss_photo = ImageTk.PhotoImage(boss_img)             
        img_label = tk.Label(header_frame, image=boss_photo, bg="black",
                            bd=2, relief="solid", highlightbackground="green", highlightthickness=2)
        img_label.image = boss_photo
        img_label.pack(side="left", padx=40)
    else:
        tk.Label(header_frame, text="[No Display PHOTO]", font=("Arial", 12),
                bg="black", fg="red").pack(side="left", padx=40)


    tk.Label(header_frame, text=f"{boss_name}", font=("Arial", 22, "bold"),
             bg="black", fg="white").pack(side="left", padx=40)

    mentee_frame = tk.Frame(root, bg="black", bd=2, relief="solid",
                            highlightbackground="green", highlightthickness=2)
    mentee_frame.pack(fill="both", expand=True, padx=30, pady=25)

    tk.Label(mentee_frame, text="MENTEES", font=("Arial", 16, "bold"),
             bg="black", fg="green").pack(anchor="nw", padx=10, pady=10)

    vars_list = []
    for idx, sub in enumerate(subordinates[boss_name], start=1):
        var = tk.BooleanVar()
        chk = ttk.Checkbutton(
            mentee_frame,
            text=f"{idx}. {sub}",
            variable=var
        )
        chk.pack(anchor="w", padx=20, pady=8)
        vars_list.append((sub, var))

    def save_attendance():
        rows = []
        if os.path.exists("attendance.csv"):
            with open("attendance.csv", "r", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        attendance_dict = {(row["Boss"], row["Subordinate"]): row for row in rows}

        for sub, var in vars_list:
            key = (boss_name, sub)
            attendance_dict[key] = {"Boss": boss_name, "Subordinate": sub,
                                    "Attendance": "P" if var.get() else ""}

        with open("attendance.csv", "w", newline="") as f:
            fieldnames = ["Boss", "Subordinate", "Attendance"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in attendance_dict.values():
                writer.writerow(row)

        print(f"Attendance updated for {boss_name}")
        root.destroy()

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 14, "bold"), padding=10)
    ttk.Button(root, text="Save Attendance",
               command=save_attendance).pack(pady=20)

    root.mainloop()

detect_faces = False
def ask_popup():
    global detect_faces
    root_prompt = tk.Tk()
    root_prompt.withdraw()
    answer = messagebox.askyesno("Face Detection", "Do you want to detect a face now?")
    detect_faces = answer
    root_prompt.destroy()

threading.Thread(target=ask_popup, daemon=True).start()

cap = cv2.VideoCapture(0)
scan_progress = 0
scan_direction = "vertical"

while True:
    ret, frame = cap.read()
    if not ret:
        break
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    if detect_faces:
        overlay = frame.copy()
        alpha = 0.3
        if scan_direction == "vertical":
            y = int(scan_progress * h)
            cv2.line(overlay, (0, y), (w, y), (0, 0, 255), 3)
            scan_progress += 0.01
            if scan_progress >= 1:
                scan_progress = 0
                scan_direction = "horizontal"
        else:
            x = int(scan_progress * w)
            cv2.line(overlay, (x, 0), (x, h), (0, 0, 255), 3)
            scan_progress += 0.01
            if scan_progress >= 1:
                scan_progress = 0
                scan_direction = "vertical"
        cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)

    results = face_mesh.process(rgb_frame)
    if results.multi_face_landmarks:
        overlay = frame.copy()
        for landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                overlay,
                landmarks,
                mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(0,0,255), thickness=2)
            )
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)

    if detect_faces:
        faces = face_recognition.face_locations(rgb_frame)
        encodings = face_recognition.face_encodings(rgb_frame, faces)

        for face_encoding in encodings:
            distances = face_recognition.face_distance([f for f in known_faces if f is not None], face_encoding)
            best_match_index = distances.argmin() if len(distances) > 0 else None

            if best_match_index is not None and distances[best_match_index] < 0.5:
                valid_faces = [i for i, f in enumerate(known_faces) if f is not None]
                boss_name = known_names[valid_faces[best_match_index]]
                print(f"Detected: {boss_name}")
                detect_faces = False
                show_attendance_window(boss_name)
                threading.Thread(target=ask_popup, daemon=True).start()
                break

    cv2.imshow("Face Detection - Futuristic Mode", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
