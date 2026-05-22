"""English back-of-card text (principle, function, example, usage) keyed by algorithm id."""

from __future__ import annotations

# Tuple: principle, function_desc, example, usage_py (usage is usually same as registry; code is universal)
ALGO_BACK_EN: dict[str, tuple[str, str, str, str]] = {
    "img_original": (
        "Untreated BGR image; input for downstream operators.",
        "Baseline to compare every algorithm against the source.",
        "Load a photo; output is still a pixel matrix.",
        "import cv2\nimg = cv2.imread('a.jpg')\ncv2.imshow('src', img)\ncv2.waitKey(0)",
    ),
    "img_rotate": (
        "Affine transform: rotate by θ around the center using a 2×3 matrix M and warpAffine.",
        "Correct orientation or build augmented samples.",
        "Rotate a landscape photo by 15° and observe crop and interpolation.",
        "import cv2\n(h,w)=img.shape[:2]\nM=cv2.getRotationMatrix2D((w/2,h/2),15,1)\nout=cv2.warpAffine(img,M,(w,h))",
    ),
    "img_scale": (
        "Resampling changes resolution: nearest, bilinear, bicubic, etc.",
        "Unify size; multi-scale pyramids.",
        "Shrink to half then enlarge and observe detail loss.",
        "import cv2\nout=cv2.resize(img,None,fx=0.5,fy=0.5,interpolation=cv2.INTER_LINEAR)",
    ),
    "img_flip_h": (
        "Mirror about the vertical mid-axis: index map i' = W-1-i.",
        "Mirror data; symmetric objects.",
        "Flip a face left–right.",
        "import cv2\nout=cv2.flip(img,1)",
    ),
    "img_flip_v": (
        "Mirror about the horizontal mid-axis.",
        "Fix upside-down images.",
        "Flip an image vertically.",
        "import cv2\nout=cv2.flip(img,0)",
    ),
    "img_add": (
        "Saturated addition cv2.add avoids uint8 wrap-around.",
        "Brighten; blend with a constant or a second image.",
        "Add a constant bias to a dark image.",
        "import cv2\nout=cv2.add(img,50)",
    ),
    "img_sub": (
        "Saturated subtraction cv2.subtract.",
        "Background differencing; highlight changes.",
        "Subtract a constant to darken the image.",
        "import cv2\nout=cv2.subtract(img,40)",
    ),
    "img_mul": (
        "Scale pixel intensities; clip to [0,255].",
        "Contrast stretch; gain.",
        "Multiply by 1.2 in float then clip to uint8.",
        "import cv2, numpy as np\nout=np.clip(img.astype(np.float32)*1.2,0,255).astype(np.uint8)",
    ),
    "img_threshold": (
        "Fixed threshold T: above T foreground, else background.",
        "Segment text or simple objects.",
        "Binarize a scanned document.",
        "import cv2\ngray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)\n_,th=cv2.threshold(gray,127,255,cv2.THRESH_BINARY)",
    ),
    "img_mask": (
        "Single-channel mask combined with bitwise AND to keep a region of interest.",
        "Cut-out; regional statistics.",
        "Threshold to a mask then keep only the object.",
        "import cv2\nmask=cv2.inRange(hsv,low,high)\nout=cv2.bitwise_and(img,img,mask=mask)",
    ),
    "img_ch_b": (
        "Split multi-channel matrix; visualize B alone.",
        "Analyze color channel; dehaze prep.",
        "Show only the blue channel.",
        "import cv2\nb,g,r=cv2.split(img)\nzeros=np.zeros_like(b)\nvis=cv2.merge([b,zeros,zeros])",
    ),
    "img_ch_g": (
        "Split and isolate the green channel.",
        "Vegetation indices; luminance proxy.",
        "Show only the green channel.",
        "import cv2\nb,g,r=cv2.split(img)",
    ),
    "img_ch_merge": (
        "cv2.merge combines single channels into multi-channel.",
        "Reassemble processed components.",
        "Merge three BGR grayscale maps.",
        "import cv2\nout=cv2.merge([b,g,r])",
    ),
    "img_hsv": (
        "HSV is more lighting-stable; inRange yields a binary mask.",
        "Color object segmentation.",
        "Extract a red bottle cap region.",
        "import cv2\nhsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)\nmask=cv2.inRange(hsv,low,high)",
    ),
    "img_affine": (
        "Affine keeps parallel lines: 6 DOF from three point pairs to M.",
        "Approximate perspective correction; alignment.",
        "Deskew slanted text.",
        "import cv2\nM=cv2.getAffineTransform(pts1,pts2)\nout=cv2.warpAffine(img,M,(w,h))",
    ),
    "img_hist_gray": (
        "Count gray levels h(k); normalize to probability.",
        "Analyze exposure; bimodal split.",
        "Under-exposed histogram clusters at the dark end.",
        "import cv2\nhist=cv2.calcHist([gray],[0],None,[256],[0,256])",
    ),
    "img_hist_color": (
        "Per-channel B/G/R histograms.",
        "Color balance analysis.",
        "Compare original vs color-cast histograms.",
        "import cv2\nh=cv2.calcHist([img],[0],None,[256],[0,256])",
    ),
    "img_hist_eq": (
        "Grayscale equalization spreads levels; color often equalizes the Y channel.",
        "Boost global contrast.",
        "Brighten a backlit face.",
        "import cv2\neq=cv2.equalizeHist(gray)",
    ),
    "img_hist_cmp": (
        "cv2.compareHist: correlation, Chi-square, Bhattacharyya, etc.",
        "Retrieval; change detection.",
        "Compare correlation of original vs equalized histograms.",
        "import cv2\nd=cv2.compareHist(h1,h2,cv2.HISTCMP_CORREL)",
    ),
    "img_q_single": (
        "Single threshold maps continuous gray to two levels.",
        "Binary segmentation.",
        "Otsu can pick T automatically.",
        "import cv2\n_,th=cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)",
    ),
    "img_q_double": (
        "Two thresholds form three bands or echo Canny hysteresis.",
        "Edge linking; layered regions.",
        "High T keeps strong edges; low T connects weak ones.",
        "import cv2\nedges=cv2.Canny(gray,t1,t2)",
    ),
    "img_thresh_zero": (
        "THRESH_TOZERO: below T set to 0; above keeps value.",
        "Suppress weak response.",
        "Soften shadow detail.",
        "import cv2\n_,th=cv2.threshold(gray,127,255,cv2.THRESH_TOZERO)",
    ),
    "img_adaptive": (
        "Local neighborhood threshold; copes with uneven lighting.",
        "Document scan; non-uniform illumination.",
        "Binarize uneven paper lighting.",
        "import cv2\nth=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)",
    ),
    "img_conv2d": (
        "Separable kernels for speed; filter2D implements linear filtering.",
        "Smoothing, sharpening, edge response.",
        "Laplacian-like kernel to emphasize edges.",
        "import cv2\nk=np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]])\nout=cv2.filter2D(gray,-1,k)",
    ),
    "morph_erode": (
        "Structuring element: per-neighborhood minimum; shrinks bright regions.",
        "Remove speckles; separate blobs.",
        "Remove small white noise on a binary image.",
        "import cv2\ner=cv2.erode(bin,kernel)",
    ),
    "morph_dilate": (
        "Per-neighborhood maximum; expands bright regions.",
        "Fill holes; connect regions.",
        "Thicken strokes.",
        "import cv2\nd=cv2.dilate(bin,kernel)",
    ),
    "morph_close": (
        "Dilate then erode: closes small holes; connects nearby objects.",
        "Fill gaps inside contours.",
        "Reconnect broken barcode vertical bars.",
        "import cv2\nout=cv2.morphologyEx(bin,cv2.MORPH_CLOSE,kernel)",
    ),
    "morph_open": (
        "Erode then dilate: removes small protrusions.",
        "Smooth contour; remove spurs.",
        "Remove salt-and-pepper bright specks.",
        "import cv2\nout=cv2.morphologyEx(bin,cv2.MORPH_OPEN,kernel)",
    ),
    "morph_grad": (
        "Dilated image minus eroded image highlights boundaries.",
        "Enhance object outlines.",
        "Binary cell boundaries.",
        "import cv2\nout=cv2.morphologyEx(bin,cv2.MORPH_GRADIENT,kernel)",
    ),
    "morph_tophat": (
        "Image minus opening highlights small details brighter than neighborhood.",
        "Dark small targets on uneven background.",
        "Tiny bright spots on a chip surface.",
        "import cv2\nout=cv2.morphologyEx(gray,cv2.MORPH_TOPHAT,kernel)",
    ),
    "morph_blackhat": (
        "Closing minus image highlights structures darker than neighborhood.",
        "Dark details; cracks.",
        "Enhance road cracks.",
        "import cv2\nout=cv2.morphologyEx(gray,cv2.MORPH_BLACKHAT,kernel)",
    ),
    "edge_laplace": (
        "Second derivative zero-crossings; sensitive to noise.",
        "Sharpening; edge localization.",
        "Simple geometric outlines.",
        "import cv2\nlap=cv2.Laplacian(gray,cv2.CV_16S,ksize=3)",
    ),
    "edge_canny": (
        "Gaussian blur, gradient magnitude/angle, double hysteresis, non-max suppression.",
        "High-quality single-pixel-wide edges.",
        "Industrial part contour extraction.",
        "import cv2\ne=cv2.Canny(gray,50,150)",
    ),
    "edge_sobel": (
        "First differences approximate partial derivatives; combine Gx, Gy magnitude.",
        "Fast gradient; directional edges.",
        "Visualize horizontal vs vertical edge components.",
        "import cv2\ngx=cv2.Sobel(gray,cv2.CV_16S,1,0,ksize=3)",
    ),
    "edge_scharr": (
        "More accurate 3×3 variant than Sobel(3); fixed kernel.",
        "Finer gradient than 3×3 Sobel.",
        "Small-structure edges.",
        "import cv2\ngx=cv2.Scharr(gray,cv2.CV_16S,1,0)",
    ),
    "img_contours": (
        "findContours extracts boundary chains from binary maps; area and perimeter.",
        "Shape analysis; object counting.",
        "Count coins.",
        "import cv2\ncnts,_=cv2.findContours(th,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)",
    ),
    "img_stitch": (
        "Feature matching estimates homography; blend projections; Stitcher high-level API.",
        "Panoramas; wide field of view.",
        "Stitch two adjacent street views.",
        "import cv2\nst=cv2.Stitcher_create()\nstatus,pano=st.stitch([a,b])",
    ),
    "filt_gray": (
        "Y = 0.299R+0.587G+0.114B (BT.601 style weights).",
        "Remove color; single channel for downstream.",
        "Black-and-white portrait style.",
        "import cv2\ng=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)",
    ),
    "filt_vintage": (
        "Color matrix or LUT: warm highlights, cool shadows.",
        "Retro tone.",
        "Old-photo look.",
        "import cv2\n# Often multiply each pixel by a 3×3 color matrix",
    ),
    "filt_emboss": (
        "Directional high-pass convolution + offset for embossed look.",
        "Artistic effect.",
        "Embossed metal logo.",
        "import cv2\nkernel=[[-2,-1,0],[-1,1,1],[0,1,2]]\nout=cv2.filter2D(gray,-1,kernel)+128",
    ),
    "filt_blur": (
        "Gaussian low-pass; σ controls bandwidth.",
        "Denoise; fake depth of field.",
        "Soften portrait skin.",
        "import cv2\nout=cv2.GaussianBlur(img,(5,5),0)",
    ),
    "filt_sharpen": (
        "Unsharp: image + k*(image − blur) or Laplacian sharpening kernel.",
        "Boost edges and texture.",
        "Compensate after blur.",
        "import cv2\nk=np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])\nout=cv2.filter2D(img,-1,k)",
    ),
    "vid_original": (
        "No processing; show the captured BGR frame as-is.",
        "Compare every operator to the raw feed.",
        "Webcam preview; check exposure and white balance.",
        "import cv2\n# Raw frame from cap.read()\nout = frame.copy()",
    ),
    "vid_gray": (
        "Per-frame cvtColor BGR→GRAY.",
        "Save compute; some detectors need luminance only.",
        "Grayscale surveillance display.",
        "import cv2\ng=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)",
    ),
    "vid_haar": (
        "Viola–Jones: integral image + Haar features + AdaBoost cascade.",
        "Real-time face/eye detection.",
        "Draw face boxes on webcam.",
        "import cv2\ncascade=cv2.CascadeClassifier(xml)\nfaces=cascade.detectMultiScale(gray,1.1,5)",
    ),
    "vid_hog": (
        "Histogram of oriented gradients + linear SVM.",
        "Classic pedestrian pipeline.",
        "Pedestrian boxes in street scenes.",
        "import cv2\nhog=cv2.HOGDescriptor()\nhog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())",
    ),
    "vid_match_sqdiff": (
        "TM_SQDIFF: sum of squared template–window differences; smaller is better.",
        "Template localization.",
        "Find a small icon in a frame.",
        "import cv2\nres=cv2.matchTemplate(img,tpl,cv2.TM_SQDIFF)",
    ),
    "vid_match_sqdiff_n": (
        "TM_SQDIFF_NORMED; more stable under lighting changes.",
        "Normalized similarity.",
        "Template match under different brightness.",
        "import cv2\nres=cv2.matchTemplate(img,tpl,cv2.TM_SQDIFF_NORMED)",
    ),
    "vid_match_ccorr": (
        "TM_CCORR: cross-correlation; larger is more similar (brightness sensitive).",
        "Simple texture alignment.",
        "Slide a subimage over a larger image.",
        "import cv2\nres=cv2.matchTemplate(img,tpl,cv2.TM_CCORR)",
    ),
    "vid_match_ccorr_n": (
        "TM_CCORR_NORMED.",
        "Correlation with less brightness bias.",
        "Logo detection.",
        "import cv2\nres=cv2.matchTemplate(img,tpl,cv2.TM_CCORR_NORMED)",
    ),
    "vid_match_coeff": (
        "TM_CCOEFF: correlation with means removed.",
        "More robust to linear lighting shifts.",
        "Industrial alignment.",
        "import cv2\nres=cv2.matchTemplate(img,tpl,cv2.TM_CCOEFF)",
    ),
    "vid_match_coeff_n": (
        "TM_CCOEFF_NORMED; very common choice.",
        "Default template matching in many apps.",
        "UI automation: find a button.",
        "import cv2\nres=cv2.matchTemplate(img,tpl,cv2.TM_CCOEFF_NORMED)",
    ),
    "vid_motion": (
        "Frame differencing or background subtraction then threshold for motion mask.",
        "Intrusion; trigger recording.",
        "Hand wave changes a region in front of the camera.",
        "import cv2\ndiff=cv2.absdiff(prev,gray)\n_,m=cv2.threshold(diff,25,255,cv2.THRESH_BINARY)",
    ),
    "vid_meanshift": (
        "Mean-shift iterations climb the density gradient in feature space to a mode.",
        "Color-histogram object tracking.",
        "Track a colored ball.",
        "import cv2\n_,win=cv2.meanShift(bp,win,term)",
    ),
    "vid_camshift": (
        "Mean-shift plus adaptive window scale/orientation.",
        "Targets that change scale.",
        "Face ellipse window as person approaches camera.",
        "import cv2\nret,win=cv2.CamShift(bp,win,term)",
    ),
    "vid_mog": (
        "Mixture of Gaussians per pixel; multiple modes adapt to slow background change.",
        "Outdoor surveillance foreground.",
        "Pedestrians with swaying trees.",
        "import cv2\nmog=cv2.bgsegm.createBackgroundSubtractorMOG()\nfg=mog.apply(frame)",
    ),
    "vid_mog2": (
        "Improved GMM; optional shadow detection.",
        "More stable foreground split.",
        "Indoor lighting drift.",
        "import cv2\nm=cv2.createBackgroundSubtractorMOG2(500,16,True)\nfg=m.apply(frame)",
    ),
    "vid_yolo_det": (
        "Ultralytics YOLO: single-stage detection; official .pt or exported ONNX/engine.",
        "Multi-class boxes and visualization.",
        "Cars and pedestrians in one street frame.",
        "from ultralytics import YOLO\nmodel = YOLO('yolo11n.pt')\nresults = model.predict(frame)\nout = results[0].plot()",
    ),
    "vid_yolo_rec": (
        "Same Ultralytics model as detection; this app summarizes class names on the recognition view.",
        "Turn detections into a readable class list for \"recognition\".",
        "Same weights as detection; overlay text like \"recognized: class A, class B\".",
        "from ultralytics import YOLO\nmodel = YOLO('yolo11n.pt')\nresults = model.predict(frame)\n# Read cls and names from results[0].boxes",
    ),
}


def algo_back_body(lang: str, spec: object) -> tuple[str, str, str, str, str]:
    """Principle, function, example, usage, optional extension — loaded from ``algo_descriptions`` CSV."""
    from cv_course.algo_descriptions import get_algo_doc_parts
    from cv_course.algo_doc_layout import normalize_algo_doc_for_display

    p, fd, ex, u, ext = get_algo_doc_parts(str(getattr(spec, "id", "")), lang)
    p2, fd2, u2 = normalize_algo_doc_for_display(lang, p, fd, ex, u, ext)
    return p2, fd2, "", u2, ""
