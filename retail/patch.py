with open('camera_worker.py', 'r') as f:
    c = f.read()

# Import qo'shish
old_import = 'from rtsp_reader import RTSPCapture'
new_import = 'from rtsp_reader import RTSPCapture\nfrom frame_annotator import FrameAnnotator'
c = c.replace(old_import, new_import)

# __init__ ga annotator qo'shish
old_init = 'self.demo_frames: dict[int, int] = {}'
new_init = 'self.demo_frames: dict[int, int] = {}\n        self.annotator = FrameAnnotator(camera["id"])'
c = c.replace(old_init, new_init)

# Detection loop da frame_detections list qo'shish
old_loop = 'current_ids: set[int] = set()'
new_loop = 'current_ids: set[int] = set()\n                frame_detections: list[dict] = []'
c = c.replace(old_loop, new_loop)

# Her box uchun detection append
old_dwell = '                    self.dwell_tracker.update(track_id, zone, demographics)'
new_dwell = '''                    frame_detections.append({
                        "track_id": track_id,
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                        "gender": gender, "age_group": age_group,
                        "is_staff": is_staff, "confidence": round(conf, 2),
                        "zone_label": zone,
                    })
                    self.dwell_tracker.update(track_id, zone, demographics)'''
c = c.replace(old_dwell, new_dwell)

# Lost tracks dan keyin annotate
old_active = '                self.active_tracks = current_ids'
new_active = '                self.annotator.annotate_and_publish(frame, frame_detections)\n                self.active_tracks = current_ids'
c = c.replace(old_active, new_active)

with open('camera_worker.py', 'w') as f:
    f.write(c)

print('Patch qilindi!')
print('annotator bor:', 'annotator' in c)