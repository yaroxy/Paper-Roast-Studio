### 5.2 MoE Infra

Training Mixture of Experts (MoE) models presents substantial challenges arising from their massive parameter scale and the inherent imbalance in expert activation. Although MoE architectures reduce per-step computation compared to dense models, the overall training process remains dominated by two sources of overhead: the computational cost of activating multiple experts and the communication burden associated with intensive inter-device data exchange. To alleviate computational overhead, we implement optimized kernel fusion for expert operations, achieving up to a  $ 3\times $  training speedup, and extend these optimizations to core modules such as self-attention and Layer Normalization, thereby improving end-to-end efficiency. To address communication inefficiencies, we design hardware-adapted infrastructures: on NPU processors, we employ a Megatron-based distributed framework that partitions both MoE and ViT across devices, combining pipeline and expert parallelism to reduce memory footprint and communication overhead through efficient weight sharing; on NVIDIA devices (e.g., H20, A100), we adopt DeepSpeed ZeRO-2 (Lan et al., 2025) with CPU offloading, which provides superior communication efficiency relative to ZeRO-3 and directly mitigates the computation–communication imbalance intrinsic to MoE training.

## 6 Experiment

In this section, we present a comprehensive experimental comparison and analysis across multiple dimensions using a wide range of LVM benchmarks

### 6.1 Evaluation Setting

We first outline the detailed evaluation settings used in our experimental analysis.

Model Zoo. We introduce the model zoo for SAIL-VL2, encompassing a range of model scales and configurations. Equipped with our SAIL-ViT model family, SAIL-VL2 employs foundational LLM components such as Qwen3-0.6B, Qwen3-1.7B, Qwen3-8B, Qwen3-16B-A2.5B, and Qwen3-30B-A3B for comprehensive pre-training. Based on the various settings of SAIL-ViT, we detail the configurations of the SAIL-VL2 zoo as follows:

- Fixed-Resolution SAIL-ViT: In this setting, we preprocess the images by cropping and resizing them to a base resolution of  $ 448 \times 448 $ . A  $ 2 \times 2 $  pixel shuffle downsampling strategy is applied to each frame to improve computational efficiency. Based on this configuration, we trained and provided the SAIL-VL2-1B, SAIL-VL2-2B, SAIL-VL2-8B, and SAIL-VL2-30B-A3B models.

- SAIL-ViT-AnyRes: This setting supports input images of arbitrary resolutions, preserving original aspect ratios while enabling more fine-grained modeling. The largest supported resolution, given a maximum input length of 16,384, is  $ 1792 \times 1792 $ . Using this approach, we trained the SAIL-VL2-AnyRes-2B model.

Furthermore, we extend the SAIL-VL2 models with a thinking version via thinking-fusion tuning (SFT-RL combined tuning). These models, marked as SAIL-VL2-2B-think, SAIL-VL2-8B-think, and SAIL-VL2-30BA3B-think, provide enhanced reasoning capabilities.

Baselines. To conduct a comprehensive performance analysis of SAIL-VL2, we present an extensive set of baselines for comparison. In the basic setting, SAIL-VL2 is compared with leading open-source and proprietary models, including, but not limited to, the Qwen2.5-VL (Bai et al., 2025), InternVL3 (Zhu et al., 2025), InternVL3.5 (Wang et al., 2025d), Ovis2 (Lu et al., 2025), and Ovis-U1 (Wang et al., 2025a). Detailed model performance comparisons are provided in Table 8, Table 9 and Table 10.

For the thinking model, we compare SAIL-VL2 with both open-source and proprietary models, such as Kimi-VL-A3B-Thinking-2506, Keye-VL-8B-Thinking OpenVLThinker-7B, and WeThink-7B. Further detailed comparisons of model performance are shown in Table 10.

Benchmarks. We perform extensive experimental comparisons and analysis across a diverse set of benchmarks, covering 106 datasets. These benchmarks are organized into four primary evaluation dimensions: General Open-source Multimodal Understanding Benchmarks, the OpenCompass evaluation system (Contributors, 2023), and open-source video understanding benchmarks:

- The General Open-source Multimodal Understanding Benchmarks encompass 72 datasets, spanning a wide range of tasks including "Multi-Image Understanding," "Multilingual Understanding," "Real-World Understanding," "Charts, Documents, and OCR Tasks," "Multimodal Reasoning