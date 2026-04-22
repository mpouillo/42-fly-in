import pyray as pr
from src.player import Player
from src.constants import CAMERA_FOVY_PERSPECTIVE, CAMERA_FOVY_ORTHOGRAPHIC


class Camera(Player):
    def __init__(self,
                 position: pr.Vector3,
                 direction: pr.Vector3,
                 orth_pos: pr.Vector2):
        super().__init__(position, direction)

        self.fovy = CAMERA_FOVY_PERSPECTIVE
        self.perspective = pr.CAMERA_PERSPECTIVE
        target = pr.vector3_add(self.position, self.direction)
        self.camera = pr.Camera3D(self.position,
                                  target,
                                  (0, 1, 0),
                                  self.fovy,
                                  self.perspective)
        self.saved_position = None
        self.saved_direction = None
        self.saved_fovy = CAMERA_FOVY_ORTHOGRAPHIC
        self.orth_pos = orth_pos

    def toggle_perspective(self):
        if self.perspective == pr.CAMERA_PERSPECTIVE:
            self.perspective = pr.CAMERA_ORTHOGRAPHIC
            self.fovy = self.saved_fovy
            self.saved_position = self.position
            self.saved_direction = self.direction
            self.position = pr.Vector3(self.orth_pos.x, 20.0, self.orth_pos.y)
            self.direction = pr.Vector3(0, -1, 0)
            self.camera.up = pr.Vector3(0, 0, -1)
        else:
            self.perspective = pr.CAMERA_PERSPECTIVE
            self.saved_fovy = self.fovy
            self.fovy = CAMERA_FOVY_PERSPECTIVE
            self.position = self.saved_position
            self.direction = self.saved_direction
            self.camera.up = pr.Vector3(0, 1, 0)

    def update(self):
        if not self.perspective == pr.CAMERA_ORTHOGRAPHIC:
            self.controls()
        else:
            scroll = pr.get_mouse_wheel_move_v()
            if scroll.y:
                self.fovy = min(45, max(1, self.fovy - scroll.y))
        self.camera.fovy = self.fovy
        self.camera.projection = self.perspective
        self.camera.position = self.position
        self.camera.target = pr.vector3_add(self.position, self.direction)
