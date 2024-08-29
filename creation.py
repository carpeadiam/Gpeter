import google.generativeai as genai
import os
import re
import pprint

genai.configure(api_key='AIzaSyDlpNp8jEAPmkim1qu4rrTF8naP1VbwcYg')
model = genai.GenerativeModel("gemini-1.5-flash")

#fileai = genai.get_file(name="sn8avh6ba0ki")

def createTopics(fileai):
    response = model.generate_content([fileai,f"You are a helpful study bot. Even if the input is insufficient, remember to always give a kind answer! First let's generate a list of subtopics from the chapter. Give back only and only a comma seperated list of subtopics. For example: Topic 1,Topic 2,Topic 3 .It is very important you follow this format so we can extract these topics with code. Thanks!"])
    topics=response.text.split(",")
    return topics

def createContent(fileai,topic):
    response = model.generate_content([fileai,f"You are a helpful study bot. Even if the input is insufficient, remember to always give a kind answer! Second let's generate some slides for each subtopic. Give back only and only the result in the following format.Also only and exactly 5 lines in a slide. Also maximum 5 slides per topic. You are welcome to add some content from outside the attached material but keep a very high proportion of content from the attached material. For example: [Topic: Topic 1 , Slides : [ (Slide-number:1,Content:[(Normal-line:Line1),(Normal-line:Line2),(Bullet-line:Line3),(Bullet-line:Line4),(Bullet-line:Line3),(Bullet-line:Line5),(Numbered-line:Line6),(Numbered-line:Line7)],Acronym-possible:True)   ,],] . Acronym possible means that is's possible to generate a good ancronym/pneumonic to remember the content. Especially useful with lists with boldened contexts or subheading type. Only give it as true when absolutely possible and meets good criteria not just every random information.It is very important you follow this format so we can extract these topics with code. REMEMBER TO ABSOLUTELY FOLLOW THE DOCUMENT PROVIDED! Also don't use too many unnecessary slides. Thanks! Here's the subtopics for this generation : {topic}"])
    return response.text

def createQuestions(fileai,topic):
    response = model.generate_content([fileai,f"You are a helpful study bot. Even if the input is insufficient, remember to always give a kind answer! Third let's generate some questions for each subtopic. The question can be either multiple choice with 4 options (and one answer) or a True or False question. Give back only and only the result in the following format. For example: [Topic: Topic 1 , Questions : [ (Question-number:1,Type:MCQ,Question:Question?,Answer:Answer,Distractors:[option1,option2,option3]),(Question-number:2,Type:MCQ,Question:Question?,Answer:Answer,Distractors:[option1,option2,option3]),(Question-number:3,Type:TrueFalse,Question:Question?,Answer:True,Distractor:False)]] It is very important you follow this format so we can extract these topics with code. REMEMBER TO ABSOLUTELY FOLLOW THE DOCUMENT PROVIDED! Thanks! Here's the subtopics for this generation : {topic}"])
    return response.text

def parse_input_string(input_string):
    # Initialize the structure
    result = {"Slides": []}

    # Parse the Topic
    topic_match = re.search(r"\[Topic:\s*(.*?),", input_string)
    if topic_match:
        result["Topic"] = topic_match.group(1).strip()

    # Parse each Slide
    slide_matches = re.finditer(r"\(Slide-number:(\d+),Content:\[(.*?)\],Acronym-possible:(True|False)\)", input_string)
    for slide in slide_matches:
        slide_number = int(slide.group(1))
        content_raw = slide.group(2).strip()
        acronym_possible = slide.group(3) == "True"

        # Parse the content within the slide
        content = []
        content_items = re.findall(r"\((.*?)\)", content_raw)
        for item in content_items:
            if "Normal-line" in item:
                content.append({"Normal-line": item.split(":")[1].strip()})
            elif "Bullet-line" in item:
                content.append({"Bullet-line": item.split(":")[1].strip()})
            elif "Numbered-line" in item:
                content.append({"Numbered-line": item.split(":")[1].strip()})

        # Add to the result structure
        result["Slides"].append({
            "Slide-number": slide_number,
            "Content": content,
            "Acronym-possible": acronym_possible
        })



    return result


def parse_quiz_string(quiz_string):
    # Regular expression to match the topic
    topic_pattern = re.compile(r"Topic:\s*(.+?),\s*Questions\s*:\s*\[")

    # Regular expression to match both MCQ and True/False questions
    question_pattern = re.compile(
        r"\(Question-number:(\d+),Type:(MCQ|TrueFalse),Question:(.*?),Answer:(.*?),(Distractors:\[(.*?)\]|Distractor:(True|False))\)"
    )

    # Extract the topic
    topic_match = topic_pattern.search(quiz_string)
    topic = topic_match.group(1) if topic_match else None

    # Extract the questions
    questions = []

    for match in question_pattern.finditer(quiz_string):
        question_number = int(match.group(1))
        question_type = match.group(2)
        question_text = match.group(3).strip()
        answer = match.group(4).strip()

        if question_type == "MCQ":
            distractors = [d.strip() for d in match.group(6).split(",")]
            questions.append({
                "Question-number": question_number,
                "Type": question_type,
                "Question": question_text,
                "Answer": answer,
                "Distractors": distractors
            })
        elif question_type == "TrueFalse":
            distractor = match.group(6)
            distractor = distractor.strip() if distractor else None
            questions.append({
                "Question-number": question_number,
                "Type": question_type,
                "Question": question_text,
                "Answer": answer,
                "Distractor": distractor
            })

    return {
        "Topic": topic,
        "Questions": questions
    }
#response=createQuestions(fileai,createTopics(fileai)[0])
#print(parse_quiz_string(response))

#def createQuiz(qnum,topics):


