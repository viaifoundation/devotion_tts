# **The Convergence of Deskside Supercomputing and Next-Generation Generative Audio: A Comprehensive Analysis of NVIDIA DGX Spark and the Late-2025 Text-to-Speech Landscape**

## **Executive Summary**

The technological landscape of late 2025 is defined by two simultaneous paradigm shifts: the democratization of data-center-grade compute through localized "edge supercomputing" hardware, and the maturation of generative audio models that have transcended the "uncanny valley" of robotic synthesis. This report provides an exhaustive analysis of this convergence, specifically examining the **NVIDIA DGX Spark**—a compact workstation powered by the **Grace Blackwell GB10 Superchip**—and its role as the premier host for a new generation of Text-to-Speech (TTS) architectures.

Central to this analysis is the evaluation and ranking of the leading TTS models released in the latter half of 2025, including **Fun-CosyVoice 3.0**, **GLM-TTS**, **Fish Speech 1.5 (OpenAudio S1)**, and **ChatTTS**. By synthesizing performance metrics such as Character Error Rate (CER), Speaker Similarity (SIM), and Real-Time Factor (RTF) with the architectural capabilities of the DGX Spark, this report establishes a definitive ranking of these technologies. Furthermore, it dissects the commercial viability of these models through the lens of complex open-source licensing frameworks (AGPL, MIT, CC-BY-NC-SA) and provides a strategic roadmap for enterprise deployment on ARM64-based accelerated computing platforms.

The findings indicate that while the NVIDIA DGX Spark offers an unprecedented 128GB of unified memory and 1 PFLOP of AI compute in a sub-200W envelope, its adoption necessitates a rigorous optimization strategy involving **TensorRT-LLM** and **FP4 quantization**. In the software domain, **Fun-CosyVoice 3.0** emerges as the technical leader in pronunciation accuracy and latency, while **MeloTTS** and **Chatterbox-ONNX** retain strategic importance for commercially restrictive environments.

## ---

**Part I: The Hardware Paradigm – NVIDIA DGX Spark and the GB10 Grace Blackwell Architecture**

The release of the NVIDIA DGX Spark marks a pivotal moment in the history of workstation computing. Historically, the dichotomy between "consumer" workstations and "enterprise" servers was defined by memory architecture and interconnect bandwidth. The DGX Spark effectively collapses this distinction, placing a miniature hyperscale node on the researcher's desk.

### **1.1 The Architecture of the GB10 Grace Blackwell Superchip**

At the heart of the DGX Spark is the **NVIDIA GB10 Grace Blackwell Superchip**, a system-on-chip (SoC) that integrates a high-performance ARM CPU and a Blackwell architecture GPU into a single package. This integration is not merely a matter of proximity but of coherence, facilitated by the **NVLink-C2C (Chip-to-Chip)** interconnect.1

#### **1.1.1 The Grace CPU: ARMv9 in the Data Science Workflow**

Unlike the x86-64 architectures that have dominated the workstation market for decades (Intel Core, AMD Ryzen/Threadripper), the GB10 utilizes the **ARMv9 architecture**. The CPU component features 20 cores, divided into a heterogeneous configuration of **10 Cortex-X925 performance cores** and **10 Cortex-A725 efficiency cores**.3

The implications of this shift to ARM64 are profound. The Cortex-X925 cores are engineered for high single-threaded performance, which is critical for the serial bottlenecks often found in AI preprocessing pipelines—such as tokenization, data cleaning, and audio resampling—before the data is handed off to the GPU.4 Meanwhile, the Cortex-A725 cores manage the operating system (NVIDIA DGX OS) and background I/O operations with exceptional power efficiency, allowing the total system thermal design power (TDP) to remain around 200W.1

However, the migration to ARM64 introduces a non-trivial software compatibility layer. While the core NVIDIA AI stack (CUDA, TensorRT, RAPIDS) is fully optimized for ARM (aarch64), legacy proprietary libraries or x86-specific SIMD (AVX-512) optimizations in third-party tools require recompilation or replacement. Developers must utilize compilers like **GCC 12.3+** or **NVIDIA HPC Compilers** with specific flags such as \-mcpu=neoverse-v2 to unlock the vector processing capabilities of the Grace CPU.5

#### **1.1.2 The Blackwell GPU: The FP4 Revolution**

The GPU component of the GB10 is built on the **Blackwell architecture**, the successor to Hopper. The defining characteristic of this architecture is the introduction of **Fifth-Generation Tensor Cores** with native support for **FP4 (4-bit floating point)** precision.2

In the context of generative AI, precision is a direct lever for capacity and speed. Previous generations relied on FP16 or BF16 (16-bit) and INT8 (8-bit) formats. The ability to execute operations in FP4 effectively doubles the theoretical throughput compared to INT8 and quadruples it compared to FP16, provided the model weights are quantized accordingly.6

* **Performance Metrics:** The DGX Spark is rated for up to **1 PFLOP (petaFLOP)** of AI performance at FP4 sparsity.3  
* **Model Capacity:** This quantization capability allows the Spark to run models with parameter counts that were previously impossible on a single node. A 200-billion parameter model, which would require \~400GB of VRAM in FP16, can be compressed to \~100GB in FP4, fitting entirely within the Spark's unified memory.4

### **1.2 The Unified Memory Architecture (UMA) Advantage**

The most disruptive feature of the DGX Spark is its memory subsystem. The GB10 features **128GB of LPDDR5X unified memory**.1 In traditional architectures (e.g., a PC with an RTX 4090), there is a stark physical and logical separation between System RAM (DDR5) and GPU VRAM (GDDR6X). Data must be copied back and forth over the PCIe bus, which introduces latency and creates a hard "VRAM Wall"—if a model is 1GB larger than the GPU's VRAM, it simply cannot run without severe performance penalties from offloading.

The DGX Spark eliminates the VRAM Wall. The CPU and GPU access the same 128GB memory pool coherently.

* **Zero-Copy Access:** Data loaded by the CPU (e.g., a massive dataset of audio files for TTS training) is instantly accessible by the GPU without a copy operation across a bus.6  
* **Bandwidth Dynamics:** The memory bandwidth is rated at **273 GB/s**.3 While this is lower than the \~1 TB/s bandwidth of high-end discrete GPU VRAM, it is significantly higher than standard CPU memory channels. For inference tasks where batch sizes are small (common in real-time TTS), the latency benefits of avoiding PCIe transfers often outweigh the raw bandwidth deficit.11

### **1.3 Networking, Scalability, and "Spark Stacking"**

NVIDIA has positioned the Spark not just as a standalone unit but as a modular component of a larger cluster. The integration of a **ConnectX-7 SmartNIC** offering **200 Gb/s** bandwidth allows for a deployment topology known as "Spark Stacking".1

Through the dual QSFP ports, two Spark units can be linked directly. This is not a standard Ethernet connection but a high-speed fabric supporting **RDMA (Remote Direct Memory Access)**.1 RDMA allows the GPU in Spark Unit A to read directly from the memory of Spark Unit B without interrupting the CPU of either unit.

* **The 256GB/2-PetaFLOP Node:** By stacking two Sparks, developers create a logical node with 256GB of unified memory and 2 PFLOPs of compute. This configuration is explicitly validated by NVIDIA to support the inference of **405-billion parameter models** (such as Llama 3.1 405B), bringing capability previously reserved for DGX H100 racks to the desktop.2

### **1.4 Physical Constraints and Thermal Engineering**

The engineering challenge of the DGX Spark was to fit this performance into a chassis measuring just **150 x 150 x 50.5 mm** (approx. 1.13 liters).3 The system operates on an external 240W power supply, with the SoC TDP configurable up to 140W.3

* **Thermal Throttling Risks:** Independent reviews have highlighted that while the active cooling system is effective for the SoC, the high density of components poses challenges for peripheral thermal management. Specifically, the single **M.2 2242 NVMe slot** has been identified as a thermal bottleneck. The smaller 2242 form factor dissipates heat less efficiently than standard 2280 drives, and under sustained write loads (such as caching datasets for training), the SSD can throttle, impacting system responsiveness.12  
* **Storage Expansion:** To mitigate this, the use of external storage via the **USB4/Thunderbolt-compatible USB-C ports** or network-attached storage (NAS) via the **10GbE or 200GbE ports** is recommended for data-intensive workloads.12

## ---

**Part II: The Generative Audio Renaissance – Analysis of Late-2025 TTS Models**

As the hardware capability to run massive models moves to the edge, the software models themselves have undergone a radical transformation. The Text-to-Speech (TTS) landscape in late 2025 has shifted away from purely acoustic parameter estimation toward large-scale generative pre-training, utilizing architectures borrowed from Large Language Models (LLMs) and Diffusion Models.

### **2.1 GLM-TTS: The Reinforcement Learning Approach (ZhipuAI)**

Released in December 2025, **GLM-TTS** from ZhipuAI represents the convergence of LLM reasoning and audio synthesis. It treats speech synthesis not just as signal processing, but as a language modeling task.13

* **Two-Stage Architecture:**  
  1. **Text-to-Token (Autoregressive):** A modified Llama backbone converts text input into discrete semantic speech tokens. This stage handles the "reasoning" of speech—understanding context, emphasis, and linguistic nuance.14  
  2. **Token-to-Waveform (Flow Matching):** A diffusion-based flow matching model converts these semantic tokens into Mel-spectrograms. This replaces traditional GAN-based vocoders, offering higher fidelity at the cost of slightly higher compute intensity.14  
* **RLHF and GRPO:** The defining innovation of GLM-TTS is the application of **Reinforcement Learning from Human Feedback (RLHF)** using **Group Relative Policy Optimization (GRPO)**. The model generates multiple candidate audio clips for a given text, which are then scored by a reward model trained on human preferences for emotion, prosody, and clarity. The GRPO algorithm optimizes the policy to maximize this reward, effectively "aligning" the TTS model in the same way ChatGPT was aligned for text.13  
* **Zero-Shot Cloning:** The model supports zero-shot voice cloning with 3-10 seconds of reference audio, achieving high speaker similarity without fine-tuning.14

### **2.2 Fun-CosyVoice 3.0: The Supervised Multi-Task Specialist (FunAudioLLM)**

**Fun-CosyVoice 3.0**, originating from Alibaba's Tongyi laboratory, focuses on robustness and latency. It addresses the "hallucination" issues common in autoregressive TTS (where the model skips or repeats words) through a rigorous supervised training regime.15

* **Finite Scalar Quantization (FSQ):** Unlike models that use continuous vectors, Fun-CosyVoice 3.0 employs a speech tokenizer with FSQ inserted into the encoder. This discretizes the speech representation into a finite codebook, which significantly improves the stability of the autoregressive generation process.17  
* **Bi-Streaming Architecture:** The model is engineered for real-time conversation. It supports "Bi-Streaming," where it can begin generating audio output while still receiving text input. This capability reduces the **Time to First Audio (TTFA)** to approximately **150ms**, making it indistinguishable from instant human response in a networked environment.15  
* **Supervised Multi-Task Learning:** The tokenizer is trained on a massive dataset (over 1.4 million hours mentioned in related research 17) across multiple tasks: Automatic Speech Recognition (ASR), Speech Emotion Recognition (SER), and Language Identification (LID). This multi-task approach forces the model to learn a more generalized and robust representation of speech.17

### **2.3 Fish Speech 1.5 / OpenAudio S1: The Instruction-Following Powerhouse**

Rebranded under the **OpenAudio** banner, the S1 model series (formerly Fish Speech) introduces the concept of "Instruction Tuning" to TTS.18

* **Dual Autoregressive (Dual-AR) Design:** OpenAudio S1 utilizes a Dual-AR architecture. While specific architectural details are proprietary, this typically implies a separation of coarse-grained semantic modeling (Stage 1\) and fine-grained acoustic modeling (Stage 2), allowing for superior decoupling of "what is said" vs. "how it is said".20  
* **Semantic Instructions:** The model's standout feature is its ability to interpret embedded tags within the text prompt. Users can inject commands like (angry), (whispering), (chuckling), or (in a hurry tone). The model modifies the prosody and timbre dynamically to match these instructions, a capability powered by its training on a dataset of 2 million hours of audio.18  
* **Distillation:** Recognizing the resource constraints of edge devices, OpenAudio offers **S1-mini** (0.5B parameters), a distilled version of the flagship **S1** (4B parameters). The S1-mini retains the core instruction-following capabilities but with a significantly reduced memory footprint, making it ideal for the DGX Spark's efficiency cores.18

### **2.4 ChatTTS and MeloTTS: The Specialized Contenders**

* **ChatTTS:** Developed by 2noise, ChatTTS is hyper-specialized for conversational dialogue. It utilizes a discrete token approach optimized to predict and insert non-verbal cues such as laughter, pauses, and filler words ("um," "uh") automatically. This creates a highly naturalistic "podcast-style" output.24  
* **MeloTTS:** Developed by MyShell.ai, MeloTTS prioritizes architectural efficiency. It is one of the few high-quality neural TTS models explicitly optimized for **CPU inference**. On the DGX Spark, MeloTTS can run entirely on the Grace CPU cores, leaving the Blackwell GPU free for heavier tasks like LLM inference or image generation.26

## ---

**Part III: The Definitive Ranking and Comparative Analysis**

The user's request for "the ranking" requires a nuanced approach. A single linear list is insufficient because the "best" model depends heavily on the specific metric: pronunciation accuracy, emotional range, or computational efficiency.

The following rankings are derived from a synthesis of the "Seed-TTS-Eval" and "test-zh" benchmark datasets provided in the research materials 15, combined with architectural analysis.

### **3.1 Primary Performance Ranking (Accuracy & Fidelity)**

This ranking prioritizes **Character Error Rate (CER)**—the standard metric for intelligibility—and **Speaker Similarity (SIM)**—the metric for cloning fidelity.

**Table 1: 2025 TTS Model Performance Matrix**

| Rank | Model | Parameters | CER (ZH) ↓ | Spk Sim (ZH) ↑ | CER (Hard) ↓ | Core Strength |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **1** | **Fun-CosyVoice 3.0 RL** | 0.5B | **0.81** | **77.4%** | **5.44** | Lowest error rate; best stability. |
| **2** | **GLM-TTS RL** | 1.5B | 0.89 | 76.4% | \- | Emotionally aligned via RLHF. |
| **3** | **VoxCPM** | 0.5B | 0.93 | 77.2% | 8.87 | Balanced performance/size. |
| **4** | **Index-TTS2** | 1.5B | 1.03 | 76.5% | 7.12 | Robust standard synthesis. |
| **5** | **Fish Speech 1.5 (S1)** | 4B / 0.5B | 1.12\* | \~79.6% | 7.59 | **Best instruction following.** |
| **6** | **FireRedTTS2** | 1.5B | 1.14 | 73.2% | \- | General purpose. |
| **7** | **Spark TTS** | 0.5B | 1.20 | 66.0% | \- | Lightweight baseline. |
| **8** | **ChatTTS** | N/A | N/A | N/A | N/A | Dialogue prosody (Benchmarks unavailable). |

**Analysis of the Ranking:**

1. **The RLHF Supremacy:** The top two models, **Fun-CosyVoice 3.0 RL** and **GLM-TTS RL**, both utilize Reinforcement Learning. This confirms that in late 2025, supervised pre-training is no longer sufficient; models must be "aligned" using human feedback to achieve sub-1.0 CER scores.13  
2. **The Efficiency Paradox:** The 0.5B parameter version of Fun-CosyVoice outperforms the 1.5B GLM-TTS in raw CER (0.81 vs. 0.89). This suggests that **data quality and tokenizer architecture** (FSQ vs. standard) matter more than raw parameter count. For the DGX Spark, this is excellent news: the highest-performing model is also the most memory-efficient.15  
3. **The "Naturalness" Caveat:** While **Fish Speech 1.5** ranks lower on CER (1.12), it reportedly achieves the highest ELO score on subjective leaderboards like TTS-Arena. This indicates that while it may make minor pronunciation errors, humans perceive its output as more "expressive" and "lifelike" due to its varied prosody and emotional range.18

### **3.2 Efficiency Ranking (Real-Time Factor & Latency)**

For edge deployment on the DGX Spark, speed is critical.

**Table 2: Inference Efficiency Profile**

| Rank | Model | Latency (Streaming) | Architecture | Spark Hardware Target |
| :---- | :---- | :---- | :---- | :---- |
| **1** | **MeloTTS** | \<100ms | Non-Autoregressive | **Grace CPU (20 Cores)** |
| **2** | **Fun-CosyVoice 3.0** | \~150ms | Bi-Streaming AR | Blackwell GPU (FP4) |
| **3** | **Fish Speech S1-mini** | \~200ms | Dual-AR (Distilled) | Blackwell GPU (FP4) |
| **4** | **GLM-TTS** | Variable | AR \+ Flow Matching | Blackwell GPU (FP16/FP4) |
| **5** | **Fish Speech S1 (4B)** | High | Dual-AR (Large) | Blackwell GPU (Unified Mem) |

**Analysis:**

* **MeloTTS** is the clear winner for ultra-low latency, capable of running purely on the CPU without consuming valuable GPU tensor resources.26  
* **Fun-CosyVoice 3.0** offers the best compromise, providing state-of-the-art quality with bi-streaming latency low enough for real-time conversation.16

## ---

**Part IV: Integration Strategy – Deploying on DGX Spark**

Deploying these models on the DGX Spark requires navigating the intersection of ARM64 compatibility, unified memory management, and NVIDIA's inference optimization tools.

### **4.1 The ARM64 Compilation Challenge**

The most immediate hurdle for deploying late-2025 AI models on the DGX Spark is the instruction set architecture. Most open-source Python wheels are pre-compiled for x86\_64 (Intel/AMD). The Spark runs on **aarch64** (ARM64).29

* **The Problem:** While PyTorch has ARM support, custom CUDA kernels—often used in the attention layers of TTS models (e.g., FlashAttention-2) or in vocoders (e.g., Vocos/BigVGAN)—may fail to load if they lack aarch64 bindings.  
* **The Solution:** Deployment must leverage **NVIDIA NGC Containers**. The container image nvcr.io/nvidia/tensorrt-llm/release:spark-single-gpu-dev provides a pre-configured environment with ARM-optimized CUDA 12.x drivers, cuDNN, and TensorRT libraries.30  
* **Build Flags:** When compiling custom extensions (e.g., for ChatTTS or Fish Speech), developers must explicitly target the Neoverse-V2 architecture of the Grace CPU. This is achieved by passing the \-mcpu=neoverse-v2 flag to the GCC or NVHPC compiler, ensuring that the compiled binaries utilize the specific SIMD (Single Instruction, Multiple Data) extensions available on the chip.5

### **4.2 TensorRT-LLM and FP4 Quantization**

To unlock the full 1 PFLOP potential of the Blackwell GPU, raw PyTorch inference is insufficient. The models must be converted to **TensorRT engines**.

1. **Quantization (FP4/FP8):** The Blackwell architecture shines at lower precisions. Using **NVIDIA TensorRT Model Optimizer**, the weights of **GLM-TTS** (1.5B) or **OpenAudio S1** (4B) can be quantized to **FP4**.  
   * *Impact:* An FP4 quantization reduces the memory bandwidth requirement by 4x compared to FP16. Given the Spark's bandwidth of 273 GB/s, this effectively quadruples the data supply rate to the compute cores, maximizing utilization.7  
   * *Trade-off:* While FP4 is revolutionary for LLMs, audio generation is sensitive to precision loss. Preliminary data suggests that **FP8** is the "sweet spot" for TTS, maintaining audio fidelity while still offering a 2x throughput gain over FP16.33  
2. **Implementation Status:**  
   * **ChatTTS:** Community implementations for TensorRT already exist, showing 3x speedups on Windows. Porting these to the Spark involves rebuilding the engine on the ARM64 host to align with the specific tensor core layout of the GB10.34  
   * **Fish Speech:** The S1 model, based on Qwen3, is compatible with TensorRT-LLM's existing Qwen support. However, the custom "Dual-AR" components require writing a custom plugin for the TensorRT builder.18

### **4.3 The "Super-Avatar" Use Case: Leveraging Unified Memory**

The true "killer app" for the DGX Spark is not just running TTS, but running a complete interactive avatar pipeline in unified memory.

* **The Pipeline:**  
  1. **Vision:** A **Llama-3.2-Vision** (11B) model processes video input.  
  2. **Brain:** A **Llama-3.3-70B** model (Quantized to 4-bit, \~40GB VRAM) generates responses.  
  3. **Voice:** **Fun-CosyVoice 3.0** (0.5B) synthesizes speech.  
* **Memory Footprint:** The total memory requirement is approximately **55-60GB**. On a standard RTX 4090 (24GB), this is impossible without agonizingly slow offloading to system RAM.  
* **Spark Advantage:** On the DGX Spark, the entire 60GB pipeline sits comfortably in the 128GB LPDDR5X pool. The unified memory architecture allows the "Brain" model to pass text tokens directly to the "Voice" model via memory pointers, eliminating the PCIe bus latency entirely.2

## ---

**Part V: Commercial, Legal, and Strategic Frameworks**

Selecting a model is not merely a technical decision but a legal one. The 2025 landscape is fragmented across three distinct licensing tiers.

### **5.1 Licensing Analysis**

**Table 3: Commercial Licensing Matrix**

| License Type | Definition | Applicable Models | Commercial Implication |
| :---- | :---- | :---- | :---- |
| **Permissive** | **MIT / Apache 2.0** | **MeloTTS** 26, **Chatterbox-ONNX** 35, **Fun-CosyVoice 3.0** (Code) | **Safe.** Can be used in closed-source, proprietary commercial products without restriction. |
| **Copyleft** | **AGPL v3** | **ChatTTS** (Code) 25 | **High Risk.** If deployed as a SaaS, source code must be open-sourced. Suitable for internal tools, risky for external products.36 |
| **Restrictive** | **CC-BY-NC-SA 4.0** | **Fish Speech / OpenAudio S1** (Weights) 38 | **Prohibited.** Commercial use requires a negotiated license or paid API usage. Legal risk is absolute for unauthorized commercial deployment. |

### **5.2 Strategic Recommendations**

Based on the intersection of performance, hardware capability, and licensing, we propose the following strategic deployment paths:

1. **For Enterprise SaaS (External Product):**  
   * **Recommendation:** **Fun-CosyVoice 3.0** or **MeloTTS**.  
   * *Reasoning:* Fun-CosyVoice offers the highest quality (Rank \#1) and typically releases under Apache 2.0 (based on Alibaba's open-source history), mitigating legal risk. MeloTTS is the CPU-safe fallback if GPU resources are constrained.  
   * *Hardware Strategy:* Use TensorRT-LLM to quantize CosyVoice to FP8 on the Blackwell GPU.  
2. **For Internal Enterprise Tools (On-Premise):**  
   * **Recommendation:** **ChatTTS**.  
   * *Reasoning:* The AGPL license allows internal use without source disclosure (as long as it's not distributed externally). Its conversational nature makes it perfect for internal training avatars or HR assistants.  
   * *Hardware Strategy:* Deploy using the standard PyTorch container on DGX Spark, as internal latency requirements are often less stringent.  
3. **For Creative/Entertainment (Games/Media):**  
   * **Recommendation:** **Fish Speech 1.5 (OpenAudio S1)**.  
   * *Reasoning:* The "Instruction Following" capability allows creative directors to "direct" the AI's emotion ((sad), (shouting)).  
   * *Path:* Users must either negotiate a commercial license with Fish Audio or use their API. For strictly internal prototyping, the local S1 model on Spark offers the best "director" experience.

## ---

**Conclusion**

The convergence of the **NVIDIA DGX Spark** and the **late-2025 TTS model generation** represents a fundamental shift in AI deployment. We have moved from a model where high-fidelity synthesis required cloud APIs to one where a deskside unit can host models that rival human expressivity.

The **DGX Spark** provides the necessary hardware foundation: an ARM64-based supercomputer with **128GB of unified memory** that breaks the VRAM barriers of consumer hardware and the bandwidth barriers of traditional workstations.

In the software domain, **Fun-CosyVoice 3.0** stands as the definitive performance champion, achieving a **CER of 0.81** and enabling real-time bi-streaming. However, the ecosystem is rich with specialized alternatives: **GLM-TTS** for RL-aligned emotionality, **Fish Speech** for instruction-based control, and **MeloTTS** for high-efficiency CPU inference.

For the researcher or engineer tasked with "combining these," the optimal path is clear: Leverage the DGX Spark's unified memory to colocate **Fun-CosyVoice 3.0** alongside a substantial LLM (like Llama 3 70B), creating a localized, ultra-low-latency, and hyper-realistic conversational agent that operates entirely within the secure, 1-liter chassis of the DGX Spark.

### **Citations**

1

#### **Works cited**

1. 128GB with 200GbE NVIDIA DGX Spark is GREAT for Local AI, accessed December 18, 2025, [https://www.youtube.com/watch?v=rKOoOmIpK3I\&vl=en](https://www.youtube.com/watch?v=rKOoOmIpK3I&vl=en)  
2. What is NVIDIA DGX Spark? \- Corsair, accessed December 18, 2025, [https://www.corsair.com/us/en/explorer/gamer/gaming-pcs/what-is-nvidia-dgx-spark/](https://www.corsair.com/us/en/explorer/gamer/gaming-pcs/what-is-nvidia-dgx-spark/)  
3. Hardware Overview — DGX Spark User Guide, accessed December 18, 2025, [https://docs.nvidia.com/dgx/dgx-spark/hardware.html](https://docs.nvidia.com/dgx/dgx-spark/hardware.html)  
4. NVIDIA DGX™ Spark Founders Edition | AI and High Performance Computing \- Leadtek, accessed December 18, 2025, [https://www.leadtek.com/eng/products/ai\_hpc(37)/nvidia\_dgx\_spark\_founders\_edition(51035)/detail](https://www.leadtek.com/eng/products/ai_hpc\(37\)/nvidia_dgx_spark_founders_edition\(51035\)/detail)  
5. Compilers — NVIDIA Grace Performance Tuning Guide, accessed December 18, 2025, [https://docs.nvidia.com/grace-perf-tuning-guide/compilers.html](https://docs.nvidia.com/grace-perf-tuning-guide/compilers.html)  
6. So what is NVIDIA Project Digits and the Blackwell Architecture? | by Dr. Nimrita Koul, accessed December 18, 2025, [https://medium.com/@nimritakoul01/so-what-is-nvidia-project-digits-and-the-blackwell-architecture-34a2d486c05d](https://medium.com/@nimritakoul01/so-what-is-nvidia-project-digits-and-the-blackwell-architecture-34a2d486c05d)  
7. How NVIDIA DGX Spark's Performance Enables Intensive AI Tasks, accessed December 18, 2025, [https://developer.nvidia.com/blog/how-nvidia-dgx-sparks-performance-enables-intensive-ai-tasks/](https://developer.nvidia.com/blog/how-nvidia-dgx-sparks-performance-enables-intensive-ai-tasks/)  
8. A Grace Blackwell AI supercomputer on your desk | NVIDIA DGX Spark, accessed December 18, 2025, [https://www.nvidia.com/en-us/products/workstations/dgx-spark/](https://www.nvidia.com/en-us/products/workstations/dgx-spark/)  
9. NVIDIA DGX Spark US \- A Grace Blackwell AI supercomputer on your desk, accessed December 18, 2025, [https://marketplace.nvidia.com/en-us/enterprise/personal-ai-supercomputers/dgx-spark/](https://marketplace.nvidia.com/en-us/enterprise/personal-ai-supercomputers/dgx-spark/)  
10. NVIDIA DGX Spark First Look: A Personal AI Supercomputer on Your Desk \- Signal65, accessed December 18, 2025, [https://signal65.com/research/nvidia-dgx-spark-first-look-a-personal-ai-supercomputer-on-your-desk/](https://signal65.com/research/nvidia-dgx-spark-first-look-a-personal-ai-supercomputer-on-your-desk/)  
11. DGX Spark is just a more expensive (probably underclocked) AGX Thor, accessed December 18, 2025, [https://www.reddit.com/r/LocalLLaMA/comments/1o7brfl/dgx\_spark\_is\_just\_a\_more\_expensive\_probably/](https://www.reddit.com/r/LocalLLaMA/comments/1o7brfl/dgx_spark_is_just_a_more_expensive_probably/)  
12. DGX Spark Deep Dive: What NVIDIA Got Right, And One Big Miss, accessed December 18, 2025, [https://www.youtube.com/watch?v=J29fhTkI0wA](https://www.youtube.com/watch?v=J29fhTkI0wA)  
13. GLM-TTS Complete Guide 2025: Revolutionary Zero-Shot Voice Cloning with Reinforcement Learning \- DEV Community, accessed December 18, 2025, [https://dev.to/czmilo/glm-tts-complete-guide-2025-revolutionary-zero-shot-voice-cloning-with-reinforcement-learning-m8m](https://dev.to/czmilo/glm-tts-complete-guide-2025-revolutionary-zero-shot-voice-cloning-with-reinforcement-learning-m8m)  
14. zai-org/GLM-TTS \- Hugging Face, accessed December 18, 2025, [https://huggingface.co/zai-org/GLM-TTS](https://huggingface.co/zai-org/GLM-TTS)  
15. FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \- Hugging Face, accessed December 18, 2025, [https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)  
16. README.md · FunAudioLLM/Fun-CosyVoice3-0.5B-2512 at main \- Hugging Face, accessed December 18, 2025, [https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/blob/main/README.md](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/blob/main/README.md)  
17. CosyVoice 3: Towards In-the-wild Speech Generation via Scaling-up and Post-training, accessed December 18, 2025, [https://arxiv.org/html/2505.17589v1](https://arxiv.org/html/2505.17589v1)  
18. Launching Fish Audio S1: A Frontier Text-to-Speech Audio Foundation Model, accessed December 18, 2025, [https://fish.audio/blog/introducing-s1/](https://fish.audio/blog/introducing-s1/)  
19. fishaudio/fish-speech: SOTA Open Source TTS \- GitHub, accessed December 18, 2025, [https://github.com/fishaudio/fish-speech](https://github.com/fishaudio/fish-speech)  
20. Fish-Speech-1.5 \- Model Info, Parameters, Benchmarks \- SiliconFlow, accessed December 18, 2025, [https://www.siliconflow.com/models/fish-speech-1-5](https://www.siliconflow.com/models/fish-speech-1-5)  
21. Fish Audio Releases OpenAudio S1: A New Benchmark for AI Voice with Professional Dubbing Actor Quality \- AI NEWS, accessed December 18, 2025, [https://news.aibase.com/news/18604](https://news.aibase.com/news/18604)  
22. Introducing S1 \- OpenAudio, accessed December 18, 2025, [https://openaudio.com/blogs/s1](https://openaudio.com/blogs/s1)  
23. fishaudio/openaudio-s1-mini \- Hugging Face, accessed December 18, 2025, [https://huggingface.co/fishaudio/openaudio-s1-mini](https://huggingface.co/fishaudio/openaudio-s1-mini)  
24. ChatTTS: Text-to-Speech For Chat, accessed December 18, 2025, [https://chattts.com/](https://chattts.com/)  
25. 2noise/ChatTTS: A generative speech model for daily dialogue. \- GitHub, accessed December 18, 2025, [https://github.com/2noise/ChatTTS](https://github.com/2noise/ChatTTS)  
26. myshell-ai/MeloTTS: High-quality multi-lingual text-to-speech library by MyShell.ai. Support English, Spanish, French, Chinese, Japanese and Korean. \- GitHub, accessed December 18, 2025, [https://github.com/myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS)  
27. The Best Open Source Text to Speech Models for Developers in 2025 \- Beam Cloud, accessed December 18, 2025, [https://www.beam.cloud/blog/open-source-tts](https://www.beam.cloud/blog/open-source-tts)  
28. FishSpeech v1.5 \- multilingual, zero-shot instant voice cloning, low-latency Only 500M params \- \#2 ranked on TTS-Arena : r/LocalLLaMA \- Reddit, accessed December 18, 2025, [https://www.reddit.com/r/LocalLLaMA/comments/1h6p335/fishspeech\_v15\_multilingual\_zeroshot\_instant/](https://www.reddit.com/r/LocalLLaMA/comments/1h6p335/fishspeech_v15_multilingual_zeroshot_instant/)  
29. Feature Request: ARM64 (Grace CPU) Support for Riva with Whisper Large-v3 Turbo, accessed December 18, 2025, [https://forums.developer.nvidia.com/t/feature-request-arm64-grace-cpu-support-for-riva-with-whisper-large-v3-turbo/354519](https://forums.developer.nvidia.com/t/feature-request-arm64-grace-cpu-support-for-riva-with-whisper-large-v3-turbo/354519)  
30. Model Orchestration and Deployment \- DGX Spark / GB10 \- NVIDIA Developer Forums, accessed December 18, 2025, [https://forums.developer.nvidia.com/t/model-orchestration-and-deployment/352153](https://forums.developer.nvidia.com/t/model-orchestration-and-deployment/352153)  
31. TRT LLM for Inference | DGX Spark \- NVIDIA NIM APIs, accessed December 18, 2025, [https://build.nvidia.com/spark/trt-llm](https://build.nvidia.com/spark/trt-llm)  
32. NVIDIA Blackwell Delivers World-Record DeepSeek-R1 Inference Performance, accessed December 18, 2025, [https://developer.nvidia.com/blog/nvidia-blackwell-delivers-world-record-deepseek-r1-inference-performance/](https://developer.nvidia.com/blog/nvidia-blackwell-delivers-world-record-deepseek-r1-inference-performance/)  
33. Maximum model size to build TRT-LLM Engine on DGX Spark? \- NVIDIA Developer Forums, accessed December 18, 2025, [https://forums.developer.nvidia.com/t/maximum-model-size-to-build-trt-llm-engine-on-dgx-spark/348981](https://forums.developer.nvidia.com/t/maximum-model-size-to-build-trt-llm-engine-on-dgx-spark/348981)  
34. warmshao/ChatTTSPlus: Extension of ChatTTS, 3x Faster on Windows, Support Voice Cloning and Mobile Deployment \- GitHub, accessed December 18, 2025, [https://github.com/warmshao/ChatTTSPlus](https://github.com/warmshao/ChatTTSPlus)  
35. onnx-community/chatterbox-ONNX \- Hugging Face, accessed December 18, 2025, [https://huggingface.co/onnx-community/chatterbox-ONNX](https://huggingface.co/onnx-community/chatterbox-ONNX)  
36. Open Source Licenses: GPL, AGPL, MIT and Apache? \- RA Marian Härtel, accessed December 18, 2025, [https://itmedialaw.com/en/open-source-licenses-gpl-agpl-mit-and-apache/](https://itmedialaw.com/en/open-source-licenses-gpl-agpl-mit-and-apache/)  
37. What are Apache, GPL and AGPL licenses and why OpenObserve moved from Apache to AGPL, accessed December 18, 2025, [https://openobserve.ai/blog/what-are-apache-gpl-and-agpl-licenses-and-why-openobserve-moved-from-apache-to-agpl/](https://openobserve.ai/blog/what-are-apache-gpl-and-agpl-licenses-and-why-openobserve-moved-from-apache-to-agpl/)  
38. fishaudio/openaudio-s1-mini at main \- Hugging Face, accessed December 18, 2025, [https://huggingface.co/fishaudio/openaudio-s1-mini/tree/main](https://huggingface.co/fishaudio/openaudio-s1-mini/tree/main)  
39. fishaudio/fish-speech-1.5 \- Hugging Face, accessed December 18, 2025, [https://huggingface.co/fishaudio/fish-speech-1.5](https://huggingface.co/fishaudio/fish-speech-1.5)  
40. OpenAudio S1 : TTS model that Laughs, Cries and every Emotion \- Medium, accessed December 18, 2025, [https://medium.com/data-science-in-your-pocket/openaudio-s1-tts-model-that-can-laugh-cry-and-every-other-emotion-2da64b9d0011](https://medium.com/data-science-in-your-pocket/openaudio-s1-tts-model-that-can-laugh-cry-and-every-other-emotion-2da64b9d0011)  
41. License terms: what about using this in a commercial product? · Issue \#531 · fishaudio/fish-speech \- GitHub, accessed December 18, 2025, [https://github.com/fishaudio/fish-speech/issues/531](https://github.com/fishaudio/fish-speech/issues/531)  
42. Request for Flexible Licensing Options for fishaudio/openaudio-s1-mini Model & Appreciation · Issue \#1096 \- GitHub, accessed December 18, 2025, [https://github.com/fishaudio/fish-speech/issues/1096](https://github.com/fishaudio/fish-speech/issues/1096)