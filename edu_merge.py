"""在注册表短描述基础上拼接教学用数学要点（中英），避免背面只有一句话。"""

from __future__ import annotations

# 按算法 id 前缀/关键词归类，拼接「原理」与「功能」后的教学段落（含公式/符号，Unicode）


def _zh_append(aid: str) -> str:
    if "hist" in aid and "cmp" not in aid and aid != "img_hist_cmp":
        if aid == "img_hist_color":
            return (
                "对 B、G、R 各通道分别统计 h_B,h_G,h_R，其中 h_c(k)=∑_{x}𝟙[I_c(x)=k]。"
                "联合可视化可观察偏色：若某通道整体平移，对应直方图会相对其它通道偏移。"
                "归一化 p_c(k)=h_c(k)/N 满足 ∑_k p_c(k)=1。"
            )
        if aid == "img_hist_eq":
            return (
                "灰度均衡映射 s(k)=(L−1)·∑_{j≤k} p(j)，L=256；彩色常在 Y 通道均衡以保持色度。"
                "逆映射为单调非减，故不引入虚假颜色边界（在 Y 上操作）。"
            )
        return (
            "离散灰度直方图 h(k)=#{像素位置 ω : I(ω)=k}，I 为灰度或分通道强度。"
            "归一化 p(k)=h(k)/N，N 为像素数，∑_k p(k)=1。"
            "累积分布 C(k)=∑_{j≤k}p(j) 用于均衡化与直方图匹配。"
        )
    if aid == "img_hist_cmp":
        return (
            "比较两分布 h₁,h₂：相关系数 d_corr=∑_k (h̃₁(k)−μ₁)(h̃₂(k)−μ₂)/(σ₁σ₂)（离散近似，OpenCV HISTCMP_CORREL）。"
            "也可用 χ²、Bhattacharyya 等度量；本演示对原图与均衡后灰度做相关。"
        )
    if aid == "img_thresh_zero":
        return (
            "THRESH_TOZERO：I'(x)=I(x)·𝟙[I(x)>T]，低于阈值的像素置 0，高于保持原值。"
            "与二值化不同，输出仍为灰度，适合抑制弱纹理而保留强边缘附近灰度。"
        )
    if aid.startswith("morph_"):
        return (
            "灰度/二值形态学在结构元素 B 上定义：腐蚀 (I⊖B)(x)=min_{b∈B} I(x+b)，"
            "膨胀 (I⊕B)(x)=max_{b∈B} I(x+b)。开闭、顶帽、黑帽均由腐蚀/膨胀复合得到。"
        )
    if aid.startswith("edge_"):
        return (
            "一阶边缘：梯度 ∇I=(∂I/∂x,∂I/∂y)，常用 |∇I|≈|G_x|+|G_y| 或 √(G_x²+G_y²)。"
            "Canny：高斯平滑后求梯度，非极大抑制，双阈值滞后连接。"
            "Laplacian：二阶算子 ∇²I，零交叉对应边缘位置。"
        )
    if aid.startswith("vid_match"):
        return (
            "模板匹配在位置 u 上计算 R(u)=Corr(T, I_{W}(u)) 或其差平方变体；"
            "归一化形式可减轻亮度线性漂移。OpenCV matchTemplate 在整幅图上滑动窗口。"
        )
    if aid in ("vid_meanshift", "vid_camshift"):
        return (
            "MeanShift 在特征空间沿密度梯度上升：x_{t+1}=x_t+ m(x_t)，m 为均值漂移向量。"
            "CamShift 在 MeanShift 基础上自适应调整搜索窗尺度与朝向。"
        )
    if aid in ("vid_mog", "vid_mog2"):
        return (
            "混合高斯背景：每个像素观测 x_t 由 K 个高斯混合建模，在线更新权重/方差以区分前景。"
            "MOG2 可显式建模阴影等改进项。"
        )
    if aid.startswith("vid_yolo"):
        return (
            "YOLO 类单阶段检测器将图像划分网格并在每个单元预测边界框与类别概率；"
            "损失通常含坐标回归、置信度与分类交叉熵。Ultralytics 封装了训练/推理与导出。"
        )
    if aid == "img_conv2d" or aid.startswith("filt_"):
        return (
            "线性滤波可写为卷积 I'(x)=∑_k I(x−k)·h(k)，离散实现即 filter2D。"
            "可分离核 h=h₁⊗h₂ 可降低复杂度。"
        )
    if aid in ("img_add", "img_sub", "img_mul"):
        return (
            "逐点算术：注意 uint8 饱和运算与 float 截断区别；cv2.add/subtract 为饱和版本，"
            "乘法常先转 float 再 clip。"
        )
    if aid.startswith("img_q") or aid in ("img_threshold", "img_adaptive", "img_thresh_zero"):
        return (
            "阈值分割将连续灰度映射到有限集合：I'(x)=255·𝟙[I(x)>T] 或分段常数；"
            "Otsu 通过最大化类间方差自动选 T。"
        )
    if aid == "img_affine" or aid == "img_rotate" or aid == "img_scale":
        return (
            "仿射变换 x'=R x + t；旋转矩阵 R(θ)=[[cosθ,-sinθ],[sinθ,cosθ]]。"
            "双线性/双三次重采样对应不同插值核。"
        )
    if aid.startswith("img_ch_") or aid == "img_hsv":
        return (
            "通道可视为 I=[I_B,I_G,I_R]；HSV 将色调 H、饱和度 S、明度 V 解耦，"
            "inRange 在柱状区域 H×S×V 上产生二值掩码。"
        )
    if aid == "img_contours":
        return (
            "轮廓可视为二值域 ∂Ω 的连通边界链；面积 A=∮_∂Ω x dy，周长可用链码近似。"
        )
    if aid == "img_stitch":
        return (
            "拼接估计单应性 H 使 x'∼H x，再经投影与融合（多频段拉普拉斯等）减轻接缝。"
        )
    if aid == "vid_motion":
        return (
            "帧差 |I_t−I_{t−1}| 或背景模型 B_t 更新后与当前帧差分，再阈值化得运动掩码。"
        )
    if aid == "vid_haar":
        return (
            "Viola–Jones：矩形 Haar 特征在积分图上 O(1) 计算，AdaBoost 级联快速拒绝非脸窗口。"
        )
    if aid == "vid_hog":
        return (
            "HOG：将图像分胞元，统计梯度方向加权直方图，块归一化后拼接成长描述子，"
            "线性 SVM 决策 f(w)=w^T φ(x)+b。"
        )
    return (
        "本算子对应 OpenCV 离散实现；一般形式可写为像素级映射 I'=F(I;θ)，θ 为参数向量。"
        "结合背面示例代码与官方文档理解数值稳定性与边界处理。"
    )


def _en_append(aid: str) -> str:
    if "hist" in aid and aid != "img_hist_cmp":
        if aid == "img_hist_color":
            return (
                "Per-channel histogram h_c(k)=∑_x 𝟙[I_c(x)=k]; normalized p_c(k)=h_c(k)/N, ∑_k p_c(k)=1. "
                "Compare B/G/R curves for color cast."
            )
        if aid == "img_hist_eq":
            return (
                "Equalization s(k)=(L−1)·∑_{j≤k} p(j) (monotone); on color, equalize Y in YCrCb to limit hue shift."
            )
        return (
            "Discrete histogram h(k) counts pixels with intensity k; p(k)=h(k)/N. "
            "CDF C(k)=∑_{j≤k}p(j) drives equalization / matching."
        )
    if aid == "img_hist_cmp":
        return (
            "Histogram distance: correlation maps to cosine similarity of mean-centered bins; "
            "OpenCV also offers Chi-square, Bhattacharyya, etc."
        )
    if aid == "img_thresh_zero":
        return (
            "THRESH_TOZERO: I'(x)=I(x)·𝟙[I(x)>T]; values below T become 0, above stay—grayscale output, not binary."
        )
    if aid.startswith("morph_"):
        return (
            "Grayscale morphology with structuring element B: erosion (I⊖B)(x)=min_{b∈B} I(x+b), "
            "dilation dual with max. Opening/closing/top-hat/black-hat are compositions."
        )
    if aid.startswith("edge_"):
        return (
            "First-order edges use ∇I; Canny chains Gaussian blur, gradient magnitude, NMS, hysteresis with T_low,T_high. "
            "Laplacian uses second-order ∇²I and zero-crossings."
        )
    if aid.startswith("vid_match"):
        return (
            "Template matching scores R(u) over shifts u; normalized variants reduce linear illumination bias."
        )
    if aid in ("vid_meanshift", "vid_camshift"):
        return (
            "Mean-shift climbs the density gradient in feature space; CamShift adapts window scale/orientation."
        )
    if aid in ("vid_mog", "vid_mog2"):
        return (
            "Gaussian mixture per pixel models background with K components; online updates separate foreground."
        )
    if aid.startswith("vid_yolo"):
        return (
            "YOLO-style detectors predict boxes and class logits on a grid; loss blends box regression, objectness, and classification."
        )
    if aid == "img_conv2d" or aid.startswith("filt_"):
        return (
            "Linear filtering I' = I * h with discrete convolution; separable kernels reduce cost."
        )
    if aid in ("img_add", "img_sub", "img_mul"):
        return (
            "Per-pixel arithmetic: mind uint8 saturation vs float clip workflows."
        )
    if aid.startswith("img_q") or aid in ("img_threshold", "img_adaptive", "img_thresh_zero"):
        return (
            "Thresholding maps intensities to a finite set; Otsu maximizes between-class variance for automatic T."
        )
    if aid in ("img_affine", "img_rotate", "img_scale"):
        return (
            "Affine map x'=R x + t; rotation R(θ) is orthogonal with det=1. Interpolation picks resampling kernel."
        )
    if aid.startswith("img_ch_") or aid == "img_hsv":
        return (
            "Channels I_B,I_G,I_R; HSV decouples hue/saturation/value—inRange defines a cylindrical ROI in HSV."
        )
    if aid == "img_contours":
        return (
            "Contours are boundary chains of binary regions; Green's theorem links area to boundary integral."
        )
    if aid == "img_stitch":
        return (
            "Stitching estimates homography H (or camera poses) then warps and blends—multi-band blending reduces seams."
        )
    if aid == "vid_motion":
        return (
            "Frame differencing |I_t−I_{t−1}| or background subtraction followed by thresholding yields motion masks."
        )
    if aid == "vid_haar":
        return (
            "Viola–Jones: integral image for fast rectangular Haar features; AdaBoost cascade rejects negatives early."
        )
    if aid == "vid_hog":
        return (
            "HOG builds cell histograms of oriented gradients, block-normalizes, concatenates; linear SVM scores f=w^Tφ+b."
        )
    return (
        "This operator is the OpenCV discrete realization; think of pixel-wise maps I'=F(I;θ) and read the API docs for stability."
    )


def enrich_zh(spec: object) -> tuple[str, str, str, str]:
    aid = str(getattr(spec, "id", ""))
    p, fd, ex, u = (
        str(getattr(spec, "principle", "")),
        str(getattr(spec, "function_desc", "")),
        str(getattr(spec, "example", "")),
        str(getattr(spec, "usage_py", "")),
    )
    ap = _zh_append(aid)
    return (p + "\n\n【数学与算法要点】\n" + ap, fd + "\n（从数学结构理解算子作用域与参数。）", ex, u)


def enrich_en_from_row(aid: str, row: tuple[str, str, str, str]) -> tuple[str, str, str, str]:
    p, fd, ex, u = row
    ap = _en_append(aid)
    return (
        p + "\n\n[Math & algorithm notes]\n" + ap,
        fd + "\n(Interpret operator behavior via its mathematical structure.)",
        ex,
        u,
    )


def enrich_en(spec: object) -> tuple[str, str, str, str]:
    aid = str(getattr(spec, "id", ""))
    p, fd, ex, u = (
        str(getattr(spec, "principle", "")),
        str(getattr(spec, "function_desc", "")),
        str(getattr(spec, "example", "")),
        str(getattr(spec, "usage_py", "")),
    )
    ap = _en_append(aid)
    return (p + "\n\n[Math & algorithm notes]\n" + ap, fd + "\n(Interpret operator behavior via its mathematical structure.)", ex, u)
