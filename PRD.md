**Product Requirements Document (PRD) for Interactive Presentation Creation Tool**

**1. Overview:**
The goal of this product is to develop a system that allows users to create in-depth presentations, complete with narration, on specified topics. Users will input a topic via free text or by uploading a document, and they can choose to specify the number of slides or allow the system to determine it.

**2. User Input:**
- Users can input a topic in natural language or upload relevant documents.
- They have the option to define the number of slides they desire or leave it to the system to decide based on the content's depth.

**3. Output:**
- The system will produce a comprehensive lesson video formatted as an MP4 file, featuring a series of slides that cover the key points of the topic. Each slide will include a narration designed to explain the content engagingly and informatively, akin to a lecture.

**4. Operational Workflow:**

**Step 1: Preparation**
- Upon receiving the user's topic, the system sends this data to the Gemini-2.5-Flash LLM. The LLM processes the input and returns a structured list of slides formatted in Python, each slide containing detailed outlines for the presentation.

**Data Structure**:
- A dictionary will be created where:
  - **Key:** Slide title or identifier.
  - **Value:** Content to be filled with a script for narration.

**Step 2: Script Generation**
- For each slide, the system will prompt the LLM with:
  - The complete context of the topic.
  - The current slide title.
  - A detailed request for a comprehensive, human-like script for narration.
- The generated scripts will be stored in the dictionary alongside their corresponding slides.

**Step 3: Voice Narration**
- Each script will then be sent to the Gemini-2.5-Flash-TTS model to produce voice narration.
- The audio for each slide will be linked to its corresponding entry in the dictionary.

**Step 4: Video Compilation**
- The system will create visual representations for each slide, incorporating the slide text.
- A timeline will be established where each slide's narration plays in sync with its visual representation. Once the narration for a slide concludes, the system will transition to the next slide.
- Finally, all the slides and their respective audio will be compiled into a continuous MP4 video.

**5. Technical Specifications:**
- **LLM Used:** Gemini-2.5-Flash for content generation.
- **TTS Model Used:** Gemini-2.5-Flash-TTS for voice narration.
- **Output Format:** MP4 video.

**6. User Experience Considerations:**
- The user interface should be intuitive, facilitating easy input of topics and preferences.
- Users will receive feedback during the preparation and generation phases, including progress updates to enhance their experience.

**7. Conclusion:**
This product aims to streamline the process of creating educational presentations, making it accessible for users to generate high-quality content with minimal effort. Leveraging advanced AI models ensures that the presentations are engaging and informative, ultimately enhancing the learning experience for users across various fields. By providing a user-friendly interface and clear operational workflow, we can cater to a wide audience, from students to professionals seeking to present complex information effectively.