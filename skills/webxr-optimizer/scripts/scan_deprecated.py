#!/usr/bin/env python3
"""Scans a WebXR codebase for removed/deprecated APIs and known XR anti-patterns.

Only mechanical, regex-detectable problems live here; judgment calls (budgets,
profiling, device quirks) stay in references/. Every rule names its replacement
and the primary source behind it, so a finding can be checked, not just trusted.

Usage: python3 scan_deprecated.py [PATH ...]   (default: current directory)
       python3 scan_deprecated.py --list-rules
Output: one `file:line: [rule-id] message (source)` per finding; exit code 1 if any.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

EXTENSIONS = {".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx", ".vue", ".svelte", ".html", ".astro"}
SKIP_DIRS = {"node_modules", "dist", "build", "out", ".git", ".next", ".nuxt", ".svelte-kit", ".turbo", "coverage", "vendor", ".vite"}
COMMENT_LINE_RE = re.compile(r"^\s*(//|\*|/\*)")


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: re.Pattern
    message: str
    source: str
    # File-level context. Anti-patterns such as calling window rAF are only wrong
    # in XR code, and some traps are defined by what a file lacks (e.g. creating
    # controller slots 0-1 but never 2-3).
    file_requires: re.Pattern | None = None
    file_lacks: re.Pattern | None = None


def rule(id, pattern, message, source, file_requires=None, file_lacks=None):
    compile_opt = lambda p: re.compile(p) if p else None
    return Rule(id, re.compile(pattern), message, source, compile_opt(file_requires), compile_opt(file_lacks))


def r3f_xr_import(names):
    # Anchored to imports from @react-three/xr: VRButton/ARButton from three/addons
    # are still current, and Controllers/Hands are common names for user components.
    return r"""import\s*\{[^}]*\b(""" + "|".join(names) + r""")\b[^}]*\}\s*from\s*['"]@react-three/xr['"]"""


XR_FILE = r"navigator\.xr|requestSession|renderer\.xr|\.xr\.enabled|XRSession|@react-three/xr"

WEBVR_SRC = "https://github.com/immersive-web/webxr/blob/main/webvr-migration.md"
WEBXR_SRC = "https://immersive-web.github.io/webxr/"
THREE_SRC = "https://github.com/mrdoob/three.js/wiki/Migration-Guide"
R3F_XR_SRC = "https://github.com/pmndrs/xr/blob/main/docs/migration/from-react-three-xr-5.md"
VISION_SRC = "https://webkit.org/blog/15162/introducing-natural-input-for-webxr-in-apple-vision-pro/"

RULES = [
    # WebVR: removed from every browser.
    rule("webvr-api",
         r"\bnavigator\.getVRDisplays\b|\bVRDisplay\w*\b|\bVRFrameData\b|\bvrdisplaypresentchange\b|\.submitFrame\s*\(",
         "WebVR was removed; use navigator.xr.requestSession() and session.requestAnimationFrame()", WEBVR_SRC),
    rule("webvr-polyfill", r"""['"]webvr-polyfill['"]""",
         "webvr-polyfill targets the removed WebVR API; use native WebXR", WEBVR_SRC),

    # Early WebXR drafts (2018-2019) still found in old tutorials.
    rule("webxr-request-device", r"\bnavigator\.xr\.requestDevice\b|\bsetCompatibleXRDevice\b",
         "XRDevice no longer exists; call navigator.xr.requestSession(mode) and gl.makeXRCompatible()", WEBXR_SRC),
    rule("webxr-supports-session", r"\.supportsSession(Mode)?\s*\(",
         "supportsSession() was removed; use navigator.xr.isSessionSupported(mode), which resolves to a boolean",
         "https://chromestatus.com/feature/5114816316047360"),
    rule("webxr-boolean-session", r"requestSession\s*\(\s*\{\s*(immersive|exclusive)\s*:",
         "requestSession takes a mode string: requestSession('immersive-vr' | 'immersive-ar' | 'inline', init)", WEBXR_SRC),
    rule("webxr-frame-of-reference",
         r"\brequestFrameOfReference\b|\bXRFrameOfReference\b|\bXRBoundedFrameOfReference\b|\bXRCoordinateSystem\b",
         "Frames of reference were renamed; use session.requestReferenceSpace('local-floor' | 'local' | ...)", WEBXR_SRC),
    rule("webxr-old-reference-space",
         r"""requestReferenceSpace\s*\(\s*(\{|['"](stage|eye-level|head-model|stationary|bounded)['"])""",
         "Old reference space type; use 'local', 'local-floor', 'bounded-floor', 'unbounded' or 'viewer'", WEBXR_SRC),
    rule("webxr-old-pose", r"\bgetDevicePose\b|\bXRDevicePose\b|\bgetInputPose\b|\bXRInputPose\b",
         "Use frame.getViewerPose(refSpace) and frame.getPose(inputSource.targetRaySpace | gripSpace, refSpace)", WEBXR_SRC),
    rule("webxr-presentation-context", r"\bXRPresentationContext\b|\boutputContext\s*:",
         "XRPresentationContext/outputContext were removed; use session.updateRenderState({ baseLayer })", WEBXR_SRC),
    rule("webxr-baselayer-assign", r"(?<!renderState)\.baseLayer\s*=(?!=)",
         "Assigning session.baseLayer no longer works; use session.updateRenderState({ baseLayer })", WEBXR_SRC),
    rule("webxr-hand-constants", r"\bXRHand\.[A-Z][A-Z_]{2,}\b",
         "XRHand joint constants were removed; use hand.get('index-finger-tip') with string joint names",
         "https://immersive-web.github.io/webxr-hand-input/"),
    rule("webxr-depth-format-preference", r"\bformatPreference\b",
         "Depth sensing renamed formatPreference to dataFormatPreference",
         "https://github.com/immersive-web/depth-sensing/commits/main"),
    rule("webxr-polyfill", r"""['"]webxr-polyfill['"]""",
         "webxr-polyfill is unmaintained (last release 2020); target native WebXR and test with IWER",
         "https://github.com/immersive-web/webxr-polyfill"),

    # three.js
    rule("three-renderer-vr", r"\brenderer\.vr\b|\.vr\.enabled\b|\bWEBVR\.\w+|/vr/WebVR(\.js)?\b",
         "three.js removed WebVR in r112; use renderer.xr.enabled = true and VRButton from three/addons/webxr/", THREE_SRC),
    rule("three-old-controllers", r"\b(ViveController|DaydreamController|GearVRController)\b",
         "Removed; use renderer.xr.getController(i) with XRControllerModelFactory", THREE_SRC),
    rule("three-vrbutton-options", r"VRButton\.createButton\s*\(\s*\w+\s*,\s*\{\s*referenceSpaceType",
         "The VRButton options argument was removed in r116; call renderer.xr.setReferenceSpaceType() instead", THREE_SRC),
    rule("three-xr-getcamera-arg", r"\.xr\.getCamera\s*\(\s*[^)\s]",
         "renderer.xr.getCamera() takes no argument since r129", THREE_SRC),
    rule("three-webgl1", r"\bWebGL1Renderer\b",
         "WebGL1Renderer was removed in r163; three.js is WebGL 2 only", THREE_SRC),
    rule("three-encoding",
         r"\.outputEncoding\b|\b(sRGBEncoding|LinearEncoding|GammaEncoding|RGBEEncoding|RGBM7Encoding|RGBM16Encoding|RGBDEncoding|LogLuvEncoding)\b",
         "Encodings were removed in r162; use renderer.outputColorSpace / texture.colorSpace (SRGBColorSpace, NoColorSpace)", THREE_SRC),
    rule("three-texture-encoding", r"\b(\w*[Mm]ap|\w*[Tt]exture|tex)\.encoding\s*=(?!=)",
         "texture.encoding was removed in r162; set texture.colorSpace = THREE.SRGBColorSpace for color maps", THREE_SRC),
    rule("three-legacy-lights", r"\.(physicallyCorrectLights|useLegacyLights)\b",
         "Removed (physicallyCorrectLights r160, useLegacyLights r165); physically correct lighting is the default", THREE_SRC),
    rule("three-render-targets", r"\bWebGLMultisampleRenderTarget\b|\bWebGLMultipleRenderTargets\b",
         "Removed; use new WebGLRenderTarget(w, h, { samples, count })", THREE_SRC),
    rule("three-geometry", r"\bnew\s+(THREE\.)?Geometry\s*\(|\bFace3\b",
         "Geometry/Face3 were removed in r125; use BufferGeometry", THREE_SRC),
    rule("three-merge-geometries", r"\bmergeBufferGeometries\b|\bmergeBufferAttributes\b",
         "Renamed to mergeGeometries / mergeAttributes (alias removed in r161)", THREE_SRC),
    rule("three-legacy-utils", r"\bTHREE\.Math\.|\bImageUtils\.loadTexture|\bBasisTextureLoader\b",
         "Removed; use THREE.MathUtils, TextureLoader, KTX2Loader", THREE_SRC),
    rule("three-legacy-build", r"examples/js/|build/three(\.min)?\.js\b",
         "examples/js (r148) and build/three(.min).js (r161) were removed; import ES modules from 'three' and 'three/addons/'", THREE_SRC),

    # @react-three/xr v6
    rule("r3f-xr-removed",
         r3f_xr_import(["Controllers", "Hands", "useController", "useHitTest", "useTeleportation", "TeleportationPlane",
                        "Ray", "VRCanvas", "ARCanvas", "XRCanvas", "DefaultXRControllers",
                        "startSession", "stopSession", "toggleSession"]),
         "Removed in @react-three/xr v6 (fails at import); see references/deprecated-apis.md section 4", R3F_XR_SRC),
    rule("r3f-xr-deprecated",
         r3f_xr_import(["VRButton", "ARButton", "XRButton", "Interactive", "RayGrab", "useInteraction", "useXREvent",
                        "useXRReferenceSpace", "useSessionModeSupported", "useSessionFeatureEnabled", "XRHandJoint",
                        "useXRHandState", "useXRControllerState", "useXRTransientPointerState", "useXRGazeState",
                        "useXRScreenInputState"]),
         "Deprecated in @react-three/xr v6; use store.enterVR()/enterAR(), R3F pointer events, useXRInputSourceState", R3F_XR_SRC),
    rule("r3f-xr-props",
         r"<XR\b[^>]*\b(foveation|frameRate|referenceSpace|onSessionStart|onSessionEnd|onVisibilityChange|onInputSourcesChange)=",
         "<XR> only takes store in v6; move these to createXRStore({ foveation, frameRate, ... }) and store.onSessionEnd()",
         R3F_XR_SRC, file_requires=r"@react-three/xr"),
    rule("r3f-xr-usexr-v5", r"\{[^{}]*\b(isPresenting|player|isHandTracking)\b[^{}]*\}\s*=\s*useXR\s*\(\s*\)",
         "useXR() changed shape in v6; use useXR(s => s.session != null), <XROrigin>, useXRInputSourceStates()", R3F_XR_SRC),

    # XR anti-patterns: valid APIs used in a way that breaks on some device.
    rule("xr-window-raf", r"(?<![\w.$])requestAnimationFrame\s*\(|\bwindow\.requestAnimationFrame\s*\(",
         "window rAF does not drive the headset; use renderer.setAnimationLoop() or session.requestAnimationFrame()",
         "https://developer.mozilla.org/en-US/docs/Web/API/WebXR_Device_API/Rendering", file_requires=XR_FILE),
    rule("xr-fixed-input-index", r"\binputSources\s*\[\s*\d+\s*\]",
         "Fixed inputSources index; iterate all sources (Vision Pro pinches arrive at index 2-3, phone taps are transient)",
         VISION_SRC),
    rule("xr-two-controller-slots", r"\.xr\.getController\s*\(\s*1\s*\)",
         "Only controller slots 0-1 are created; three.js drops Vision Pro pinches at index 2-3 (create 0..3)",
         VISION_SRC, file_lacks=r"\.xr\.getController\s*\(\s*([23]|[A-Za-z_$][\w$]*)\s*\)"),
    rule("xr-required-optional-feature",
         r"""requiredFeatures\s*:\s*\[[^\]]*['"](hand-tracking|hit-test|anchors|depth-sensing|dom-overlay|plane-detection|mesh-detection|light-estimation|camera-access|layers)['"]""",
         "Required feature rejects the whole session on devices without it (e.g. visionOS); keep it required only if the app cannot run without it, else make it optional and check session.enabledFeatures",
         WEBXR_SRC),
    rule("xr-webgl1-context", r"""getContext\s*\(\s*['"](webgl|experimental-webgl)['"]""",
         "WebGL 1 context in XR code: no multiview, and three.js r163+ requires WebGL 2; use getContext('webgl2') and await gl.makeXRCompatible()",
         "https://developers.meta.com/horizon/documentation/web/web-multiview/", file_requires=XR_FILE),
]


def iter_files(paths):
    for root in paths:
        root = Path(root)
        if root.is_file():
            yield root
            continue
        for p in sorted(root.rglob("*")):
            if p.suffix in EXTENSIONS and p.is_file() and not SKIP_DIRS.intersection(p.parts):
                yield p


def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    findings = []
    lines = text.splitlines()
    active = [r for r in RULES
              if (r.file_requires is None or r.file_requires.search(text))
              and (r.file_lacks is None or not r.file_lacks.search(text))]
    for r in active:
        for m in r.pattern.finditer(text):
            n = text.count("\n", 0, m.start()) + 1
            if COMMENT_LINE_RE.match(lines[n - 1]):
                continue
            findings.append((path, n, r))
    return sorted(findings, key=lambda f: (f[1], f[2].id))


def main(argv):
    if "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return 0
    if "--list-rules" in argv:
        for r in RULES:
            print(f"{r.id}: {r.message} ({r.source})")
        return 0
    findings = [f for p in iter_files(argv[1:] or ["."]) for f in scan_file(p)]
    for path, n, r in findings:
        print(f"{path}:{n}: [{r.id}] {r.message} ({r.source})")
    if findings:
        print(f"\n{len(findings)} finding(s).", file=sys.stderr)
        return 1
    print("OK: no deprecated WebXR APIs or known anti-patterns found.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
