# DigiPhant setup and implementation record

## Source and environment

- Instructor source: `https://github.com/kommanderpi/studentstarter`
- Source commit: `4e6dab5271c618d1c0bfb2022c41c0d37cd8d69f`
- Working branch: `feature/collective-pause-gesture`
- Unity project root: `work/DigiPhantUnity`
- URP template: 17.6.0
- Selected editor version: 6000.6.10f1
- Detected compatible Python: `/opt/homebrew/bin/python3.14`
- Python environment: `DigiPhantStarter/Tracking/.venv`
- Imported assets: `Assets/Elephant`, `Assets/DigiPhant`, `Assets/SavannahCourse`
- Student scene copy: `Assets/StudentWork/Scenes/MammothDigiPhant.unity`

The requested public fork now exists at
`https://github.com/cora-lee/studentstarter`. The branch
`feature/collective-pause-gesture` was created there. Local Git commits could not
yet be uploaded because terminal Git has no GitHub credential and Chrome blocks
local file upload until the ChatGPT extension's “Allow access to file URLs”
setting is enabled.

## Added MediaPipe Vision Task: Gesture Recognizer

The existing Pose Landmarker remains responsible for body control and performer
identity. A separate MediaPipe Gesture Recognizer task detects the canned hand
gestures and associates each detected hand with the nearest assigned Pose wrist.
The UI can therefore show results such as `P2 · L Open_Palm 0.91`.

The functional team gesture is collective pause: every selected performer shows
at least one confident `Open_Palm` for 0.6 seconds. The bridge then sends
`teamPause: true` in the existing version-1 UDP packet.

Unity activates the pause only when every selected performer slot is present and
fresh. Locomotion stops immediately, gesture-driven body controls ease toward
neutral, and the on-screen panel shows the pause state. Lowering either hand
releases the pause without changing neutral calibration, performer assignment, or
the existing division of elephant controls.

Low-confidence, non-finite, or spatially distant hand results are not assigned to
a performer and cannot activate the gesture. The bundled Gesture Recognizer model
SHA-256 is `97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482`.

## Data path

1. `Tracking/bridge.py` runs the existing MediaPipe Pose Landmarker.
2. Gesture Recognizer classifies up to eight hands in the same unmirrored frame.
3. Each detected hand is matched to the nearest visible left/right Pose wrist.
4. `CollectivePauseDetector` requires a stable 0.6-second all-performer open-palm vote.
5. The bridge sends the same localhost UDP snapshot with gesture fields and optional `teamPause`.
6. `DigiPhantController` validates complete/fresh team participation.
7. `DigiPhantLocomotion` stops travel immediately while the pause is active.

No second webcam reader, cloud image upload, or competing Unity input controller
was added. Pose and Gesture Recognizer process the same local frame.

## Tests actually run

- PASS: all 14 Python tests, including gesture-to-wrist association, rejection of
  low-confidence/distant gestures, debounce timing, role tracking, preview JPEG
  transport, and recording export timing/error handling.
- PASS: MediaPipe 0.10.35 and OpenCV 4.14.0.94 installed with no broken requirements.
- PASS: bundled Gesture Recognizer model loaded with `num_hands=8`.
- PASS: the real default camera opened and continuously processed frames through
  Pose Landmarker and Gesture Recognizer together in one-person upper-body mode.
  The process was stopped manually after startup; no human gesture result was
  claimed from this unattended check.
- PASS: `py_compile` for all tracking and recording Python files.
- PASS: `git diff --check`.
- PASS: direct C# compilation of DigiPhant runtime, editor validation, and vendor
  elephant and Savannah editor scripts against Unity 6000.6.10f1 assemblies.
- PASS: Unity 6000.6.10f1 was reinstalled and a clean smoke project imported and
  exited in batch mode with return code 0.
- PASS: the real project imported and compiled in Unity 6000.6.10f1 after adding
  the built-in `com.unity.modules.screencapture` dependency required by the recorder.
- PASS: Savannah was injected into the copied mammoth scene and its official
  validator passed: 18 trees, 4 landmarks, 130 renderers, 4,852 triangles, and no
  generated behaviours. A unique pre-injection scene backup was created.
- PASS: built-in DigiPhant template and locomotion validation completed with return
  code 0, covering rig control, UDP, presets, gaits, turns, additive gestures,
  compound inputs, tracking loss, limits, and reset.
- FIXED: the supplied seated-input validation now restores Camera mode after its
  Test Sliders step; the complete suite then passed.
- NOT RUN: interactive UDP-to-Unity Play mode, three-person gesture recognition,
  human course traversal, or a real Game-view MP4 recording.

## Required live verification

1. Personally review and accept the first-run Unity Editor Software Terms.
2. Open `Assets/StudentWork/Scenes/MammothDigiPhant.unity` if needed.
3. Select the intended performer count, switch to Camera, and calibrate.
4. Confirm ordinary individual controls still map to the documented roles.
5. Have every performer show an open palm for at least 0.6 seconds. Confirm the UI
   says `COLLECTIVE PAUSE ACTIVE`, travel stops without a forward lurch, and body
   controls settle toward neutral.
6. Have one person lower or close the hand. Confirm control resumes without recalibration.
7. Repeat in seated mode and after brief occlusion. A missing performer must not
   leave pause active.
8. Navigate the same scene's course. The course is static and has no obstacle
    collision or navigation logic, so describe the result as course traversal,
    not autonomous obstacle avoidance.
9. Record and inspect the final MP4, then upload it to the team Drive location.

## Known limits

- Gesture-to-person ownership is inferred from the nearest visible Pose wrist;
  crossings and hand overlap can still cause ambiguity.
- The pause is cooperative by design: all selected performers must participate.
- Performer identity is still position-based, not biometric.
- The starter's existing occlusion, flat-plane locomotion, and no-foot-IK limits
  remain unchanged.

