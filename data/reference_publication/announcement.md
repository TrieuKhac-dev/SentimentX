# Applying Prompt Engineering to Sentiment Analysis of Vietnamese Reviews

Huynh Thi Cam Dung¹, Mai Dinh Vinh², Nguyen Hong Vu¹, Vu Phu Loc¹(B), and Thien Khai Tran¹

¹ Faculty of Information Technology, Ho Chi Minh City University of Industry and Trade, Ho Chi Minh City, Vietnam  
{dunghtc, vunh, locvp, thientk}@huit.edu.vn

² Intelligent Data Processing System Research Group, Ho Chi Minh City, Vietnam  
business@ducksabervn.com

## Abstract

This study applies aspect-based sentiment analysis to Vietnamese lipstick reviews collected from an e-commerce platform. Utilizing a dataset of 16,227 reviews, we leverage large language models (LLMs), such as GPT, with zero-shot, one-shot, and five-shot inference strategies to extract product aspects and classify sentiments. The experimental results demonstrate that the five-shot approach achieves high accuracy (ranging from 92.86% to 100%) across various aspects, including price, packaging, texture, scent, and longevity. These findings highlight the potential of LLMs in processing Vietnamese language, particularly for product review analysis in the context of e-commerce.

**Keywords:** coreference resolution · sentiment analysis · large language model · e-commerce

## 1. Introduction

In domains such as education, customer service, finance, healthcare, and e-commerce, the demand for natural language processing (NLP) is steadily increasing. Traditional approaches, including Naive Bayes, SVM, Logistic Regression, as well as deep learning models such as CNN, RNN, and BiLSTM, have previously been applied to sentiment analysis tasks. However, these methods typically require complex preprocessing steps and rely heavily on handcrafted features and large labeled datasets.

Recently, LLMs, particularly those based on the Generative Pre-trained Transformer (GPT) architecture, have demonstrated remarkable performance due to their ability to understand context and generate natural language. GPT can handle a wide range of tasks—such as text classification, named entity recognition, machine translation, report generation, and dialogue simulation—through simple prompt engineering without the need for task-specific fine-tuning. A prominent advantage of GPT lies in its ability to perform zero-shot, one-shot, or few-shot learning, significantly reducing the need for labeled data in real-world deployment scenarios. This capability enables the model to rapidly adapt to new tasks while minimizing training costs.

In this study, we leverage GPT to perform aspect-based sentiment analysis (ABSA) based on product reviews, employing the Chain of Thought technique in combination with zero-shot, one-shot, and five-shot strategies. Experimental results indicate that GPT not only achieves high accuracy but also demonstrates flexibility and strong adaptability to the Vietnamese language context.

The remainder of this paper is organized as follows: Sect. 2 presents related work; Sect. 3 describes the proposed method and experimental results; and finally, Sect. 4 concludes the paper.

## 2. Related Work

The emergence of LLMs has opened up new opportunities for ABSA in international research. Approaches such as prompt-based learning, self-refinement, and data synthesis are increasingly being employed to address this task.

The study by Qihuang Zhong et al. [5] proposed an iterative data generation (IDG) approach that produces labeled data through repeated feedback loops from LLMs. The model not only predicts labels but also refines its responses with each iteration. This method achieved performance comparable to that of four real-world ABSA benchmark datasets. Similarly, Pandit, T. [6] generated multi-domain conversational data for ABSA training using GPT-4. This demonstrates the flexibility and high generalizability of the synthesized data, as validated by several state-of-the-art models such as Gemini 1.5 Pro, Claude 3.5, and DeepSeek-R1.

Hua Y. C. [7] conducted a comprehensive survey on ABSA, in which the authors categorized various approaches, representation techniques, and deep learning models, while also highlighting the growing role of LLMs. This work serves as a valuable foundational reference for researchers aiming to navigate and develop strategies within this field.

In addition, Nguyen et al. (2024) [8] demonstrated that ABSA can be applied in recommender systems. This can be achieved by combining sentiment analysis with matrix factorization techniques to improve the accuracy of mobile application recommendations. In another case, Jazuli, A. et al. [9] identified aspects and sentiments in student feedback in Indonesia using the BERT model. This indicates that such models are effective in conveying meaning in low-resource language contexts and could be similarly applied to Vietnamese.

In summary, the aforementioned national and international studies highlight the strong potential of LLMs in the field of ABSA. Furthermore, they demonstrate that deep learning models, data generation techniques, and practical applications are being leveraged to optimize sentiment analysis in specific contextual settings.

## 3. Prompting Method and Experiments

### 3.1. Prompting Method

We conducted experiments with three different strategies to evaluate the effectiveness of LLMs in the task of ABSA:

- **COT with zero-shot:** This approach uses Chain-of-Thought prompting to guide the model through step-by-step reasoning for extracting aspect–sentiment pairs, without providing any prior examples.
- **COT with one-shot:** Similar to the zero-shot strategy, but with the addition of a single example to help the model understand the processing pattern.
- **COT with five-shot:** Similar to the previous approach, but with the addition of five diverse examples to help the model learn from a wider range of scenarios.

The prompt template is as follows:

> [Prompt template is presented in the source document as a figure/image.]

### Applying Chain of Thought (step-by-step reasoning)

> [Chain-of-Thought prompting content is presented in the source document as a figure/image.]

### 3.2. Experiments

#### 3.2.1. Dataset

This paper conducts experiments and evaluations on a Vietnamese dataset constructed from beauty product reviews—specifically lipstick—collected from the Shopee e-commerce platform. The dataset was created to support the task of ABSA in the context of e-commerce. This constitutes a significant contribution, as at the time of the study, there were few large-scale Vietnamese datasets available in the beauty domain.

The dataset contains **32,775 aspect–sentiment pairs** extracted from **16,227 reviews** related to nine different types of lipsticks. It is used to support two main tasks: aspect detection and sentiment classification.

- **Aspect detection task:** Identify specific product aspects mentioned in each review. The labeled aspects include:
  - Smell
  - Price
  - Shipping
  - Colour
  - Packing
  - Texture
  - Staying power
- **Sentiment classification task:** Assign a sentiment label to each identified aspect using two polarity levels: positive and negative.

The colour aspect is the most frequently mentioned. According to the dataset, it appears in over 7,000 reviews—accounting for nearly 50% of the total—indicating that color is the most critical factor for customers when choosing lipstick. The distribution of each aspect and its associated sentiment is presented in Table 1 and Fig. 1. Overall, positive sentiment labels dominate across all aspects.

**Table 1. Sentiment distribution by aspect**

| Aspect | Positive | Negative | Total |
|---|---:|---:|---:|
| StayingPower | 1,521 | 940 | 2,461 |
| Texture | 3,545 | 796 | 4,341 |
| Smell | 2,341 | 440 | 2,781 |
| Price | 3,238 | 21 | 3,259 |
| Colour | 6,315 | 662 | 6,977 |
| Shipping | 3,435 | 1,692 | 5,127 |
| Packing | 2,933 | 101 | 3,034 |

Sentiment differences are particularly evident in aspects such as price and packing. E-commerce platforms often offer lower prices compared to traditional retail stores, which contributes to a high proportion of positive reviews. Meanwhile, packing is a controllable factor that plays a key role in forming a strong first impression on customers and also receives a high rate of positive feedback.

Overall, the number of positive reviews significantly outweighs the number of negative ones, as evidenced by **18,694 positive reviews** compared to **3,715 negative reviews** in the training set [1]. The definitions of each aspect are presented in Table 2.

**Table 2. Aspect definitions**

| Aspect | Definition |
|---|---|
| Smell | The review refers to the scent of the lipstick. |
| Colour | The review refers to the color of the lipstick, such as whether it is light or dark. |
| Texture | The review refers to the properties and quality of the lipstick, such as its moisture or dryness. |
| Price | The review refers to the price of the lipstick, assessing whether it is reasonable or not. |
| Stayingpower | The review refers to the color longevity of the lipstick on the lips. |
| Shipping | The review refers to the delivery service, such as delivery time or the courier’s attitude. |
| Packing | The review refers to the packaging quality, such as whether the product was carefully packed. |

#### 3.2.2. Experimental Environment

In this study, experiments were conducted using the following environments and libraries:

- **Google Colab:** used as the execution environment for model experimentation
- **GPT:** GPT-4o-mini
- **Supporting libraries:** Python, OpenAI SDK, Pandas, Scikit-learn

Upon completion of the experiments, we evaluated the effectiveness of the methods applied to LLMs for the ABSA task, based on the aspect and sentiment labels predicted by the model.

**Data preparation for comparison**

- **Ground-truth (GT) set:** the original dataset manually annotated.
- **Prediction (Pred) set:** the predicted results generated by the model.

This study focuses on seven main product aspects during the evaluation process: **SMELL, PRICE, TEXTURE, COLOUR, STAYINGPOWER, PACKING, SHIPPING**.

Samples associated with the **OTHERS** aspect and those labeled with **neutral** sentiment were excluded from the evaluation dataset to ensure consistency in assessment and to focus on the two most critical sentiment polarities. This filtering process enhanced the model’s ability to classify sentiment between the two targeted categories:

- Positive
- Negative

**Evaluation methodology**

For each aspect, the evaluation procedure was carried out as follows:

1. Retain only the samples where both the ground-truth and predicted labels fall into the two sentiment classes: positive and negative.
2. Count the number of valid samples for each aspect and sentiment label.
3. Count the number of samples where the model’s predicted sentiment exactly matches the ground-truth label.

The class-wise accuracy for each sentiment label is computed using the following formula:

$$
Accuracy_{sentiment} =
\frac{\text{Number of correctly predicted samples}_{sentiment}}
{\text{Total number of samples}_{sentiment}}
\times 100\%
$$

**Metric Calculation: Accuracy, Recall, Precision and F1-score**

- **Accuracy:** The proportion of correct predictions over the total number of predictions.
- **Recall:** The proportion of correctly predicted instances over the actual number of instances in a given class.
- **Precision:** The proportion of correctly predicted instances over the total number of predicted instances for a given class.
- **F1-score:** The harmonic mean of Recall and Precision, commonly used when both metrics need to be balanced.

#### 3.2.3. Experimental Results

**Table 3. Class-wise accuracy for each sentiment label**

| Aspect | COT + 0-shot Accuracy (%) | COT + 1-shot Accuracy (%) | COT + 5-shot Accuracy (%) |
|---|---:|---:|---:|
| Smell | 94.59 | 96.15 | 92.86 |
| Price | 97.22 | 100 | 100 |
| Texture | 94.12 | 100 | 100 |
| Colour | 97.37 | 96.61 | 94.74 |
| Stayingpower | 100 | 94.12 | 92.86 |
| Packing | 98.25 | 98.11 | 100 |
| Shipping | 100 | 98.89 | 96.70 |

Experimental results indicate that LLMs, when combined with the COT technique and 0-shot, 1-shot, and 5-shot strategies, achieved high accuracy across most aspects of the ABSA task (Table 3).

Under the COT + 0-shot strategy, the model achieved perfect accuracy (100%) in aspects such as staying power and shipping, while maintaining over 94% accuracy across other aspects.

With the COT + 1-shot strategy, incorporating a single illustrative example improved accuracy in aspects such as price and texture to 100%, while still maintaining high performance across other aspects.

Providing more diverse examples, particularly in the COT + 5-shot strategy, enabled the model to achieve 100% accuracy in more challenging aspects such as price, colour, and packing. However, a slight decrease in accuracy was observed in certain aspects such as smell and staying power, suggesting that supplying too many examples does not necessarily benefit all aspects equally (Tables 4, 5, and 6).

**Table 4. Evaluation Results for COT + 0-shot**

| Aspect | Positive Precision (%) | Positive Recall (%) | Positive F1-score (%) | Negative Precision (%) | Negative Recall (%) | Negative F1-score (%) |
|---|---:|---:|---:|---:|---:|---:|
| SMELL | 97.06 | 97.06 | 97.06 | 66.67 | 66.67 | 66.67 |
| PRICE | 100 | 97.22 | 98.59 | 0 | 0 | 0 |
| TEXTURE | 92.68 | 100 | 96.20 | 100 | 76.92 | 86.96 |
| COLOUR | 100 | 97.10 | 98.53 | 77.78 | 100 | 87.50 |
| STAYINGPOWER | 100 | 100 | 100 | 100 | 100 | 100 |
| PACKING | 100 | 98.18 | 99.08 | 66.67 | 100 | 80 |
| SHIPPING | 100 | 100 | 100 | 100 | 100 | 100 |

**Table 5. Evaluation Results for COT + 1-shot**

| Aspect | Positive Precision (%) | Positive Recall (%) | Positive F1-score (%) | Negative Precision (%) | Negative Recall (%) | Negative F1-score (%) |
|---|---:|---:|---:|---:|---:|---:|
| SMELL | 100 | 96 | 97.06 | 50 | 100 | 66.67 |
| PRICE | 100 | 100 | 100 | 0 | 0 | 0 |
| TEXTURE | 100 | 100 | 100 | 100 | 100 | 100 |
| COLOUR | 100 | 96.23 | 98.08 | 75 | 100 | 85.71 |
| STAYINGPOWER | 100 | 92.31 | 96 | 80 | 100 | 88.89 |
| PACKING | 100 | 98.04 | 99.01 | 66.67 | 100 | 80 |
| SHIPPING | 100 | 98.44 | 99.21 | 96.30 | 100 | 98.11 |

**Table 6. Evaluation Results for COT + 5-shot**

| Aspect | Positive Precision (%) | Positive Recall (%) | Positive F1-score (%) | Negative Precision (%) | Negative Recall (%) | Negative F1-score (%) |
|---|---:|---:|---:|---:|---:|---:|
| SMELL | 96.15 | 96.15 | 96.15 | 50 | 50 | 50 |
| PRICE | 100 | 100 | 100 | 0 | 0 | 0 |
| TEXTURE | 100 | 100 | 100 | 100 | 100 | 100 |
| COLOUR | 100 | 94.12 | 96.97 | 66.67 | 100 | 80 |
| STAYINGPOWER | 100 | 90 | 94.74 | 80 | 100 | 88.89 |
| PACKING | 100 | 100 | 100 | 100 | 100 | 100 |
| SHIPPING | 96.88 | 98.41 | 94.74 | 96.30 | 92.86 | 94.55 |

The experimental results demonstrate that the model achieved relatively high Precision, Recall, and F1-scores across various aspects under all evaluated strategies. The model performed exceptionally well on quantitatively explicit aspects such as price, packing, and shipping, with most metrics reaching the maximum value of 100%.

However, for more complex aspects such as smell, texture, colour, and staying power, the model faced greater challenges. This is particularly evident when handling cases with negative sentiment labels. In some instances, the F1-score for negative labels dropped significantly—even under the 5-shot prompting strategy, it reached only around 50%.

## 4. Conclusion

This study has demonstrated the effectiveness of LLMs in ABSA on Vietnamese product review data. By leveraging prompting techniques in combination with COT reasoning and 0-shot, 1-shot, and 5-shot strategies, the model achieved high accuracy, particularly in quantitative aspects such as price, packing, and shipping. Although performance slightly decreased for more subjective aspects, the results still highlight the strong potential of LLMs for Vietnamese NLP tasks. In the future, optimizing prompting strategies and diversifying example inputs may further enhance the model’s effectiveness in handling more complex aspects.

## References

1. Tran, Q.L., Le, P.T.D., Do, T.H.: Aspect-based sentiment analysis for Vietnamese reviews about beauty product on E-commerce websites. In: Proceedings of the 36th Pacific Asia conference on language, information and computation, pp. 767–776. Association for Computational Linguistics, Manila, Philippines (2022, October)
2. Shah, F. A., Sabir, A., & Sharma, R. (2024). A Fine-grained Sentiment Analysis of App Reviews using Large Language Models: An Evaluation Study. arXiv preprint: arXiv:2409.07162.
3. Huang, J., Chang, K.C.: Towards Reasoning in large Language Models: A survey. In: Findings of the Association for Computational Linguistics: ACL 2022, pp. 1049–1065. Toronto, Canada (2023). https://doi.org/10.18653/v1/2023.findings-acl.67
4. Kerner, S. M. (2025, January 22). GPT-4o explained: Everything you need to know. WhatIs. https://www.techtarget.com/whatis/feature/GPT-4o-explained-Everything-you-need-to-know
5. Qihuang Zhong, Haiyun Li, Luyao Zhuang, Juhua Liu, Bo Du. Iterative Data Generation with Large Language Models for Aspect-based Sentiment Analysis. https://arxiv.org/html/2407.00341v2
6. Pandit, T., Raval, M., & Upadhyay, D. (2025). Multi-Domain ABSA Conversation Dataset Generation via LLMs for Real-World Evaluation and Model Comparison. arXiv preprint: arXiv:2505.24701.
7. Hua, Y.C., Denny, P., Wicker, J., Taskova, K.: A systematic review of aspect-based sentiment analysis: domains, methods, and trends. Artificial Intelligence Review 57(11) (2024). https://doi.org/10.1007/s10462-024-10906-z
8. Nguyen, V.Q., Tran, K.N., Nguyen, T.S.: A study on hybrid recommend system combined sentiment analysis with matrix factorization. Ho Chi Minh City Open University Journal of Science and Engineering Technology 14(2), 48–58 (2024).
9. Jazuli, A., Widowati, & Kusumaningrum, R.: Optimizing aspect-based sentiment analysis using BERT for comprehensive analysis of Indonesian student feedback. Applied Sciences 15(1), 172 (2024).
