from dotenv import load_dotenv
from fasthtml.common import *
import google.generativeai as genai
import os
from creation import createContent, parse_input_string,createTopics ,createQuestions ,parse_quiz_string
import json
import random

load_dotenv()

app, rt = fast_app()

messages = []
sample_file = None
current_topic_index = 0
current_slide_index = 0
current_question_index=0
topic_contents = []

genai.configure(api_key='NOAPIKEY4U')
model = genai.GenerativeModel("gemini-1.5-flash")

headers = [
    Script(src="https://cdn.tailwindcss.com"),
    Link(
        rel="stylesheet",
        href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css",
    ),
    Link(rel="icon", href="pirate.png", type="image/png"),
    Script(src="https://unpkg.com/htmx.org@1.6.1/dist/htmx.min.js"),
    Script(src="https://code.jquery.com/jquery-3.6.0.min.js"),
Link(
    rel="stylesheet",
    href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap",
),
Script(
    """
    function readSlideContent(slide_id) {
        let contentContainer = document.getElementById('slide-content-' + slide_id);
        let contentText = contentContainer.textContent || contentContainer.innerText;
        let speech = new SpeechSynthesisUtterance(contentText);
        speechSynthesis.speak(speech);
    }
    """
)

]


def Slide(header, content, slide_id):
    return Div(
        Div(header, cls="text-2xl font-bold text-center text-orange-950 m-6 mb-12 ", style="font-family: 'Playfair Display', serif;"),
        Div(id=f"slide-content-{slide_id}", cls="text-lg text-left mt-4"),  # Removed margin to prevent centering
        Button("Listen", cls="btn btn-info mt-4", onclick=f"readSlideContent('{slide_id}')"),  # TTS Button
        cls="h-5/6 w-full flex flex-col items-center text-black shadow-md bg-amber-50 p-4 rounded-lg",
        style="justify-content: flex-start;"  # Align content to the top
    )


def ChatMessage(msg, is_human):
    bubble_class = "chat-bubble-primary bg-indigo-300 text-black" if is_human else "chat-bubble-secondary bg-fuchsia-300 text-black"
    align_class = "chat-end" if is_human else "chat-start"
    return Div(
        Div(
            Div(msg, cls=f"chat-bubble {bubble_class}"),
            cls=f"chat {align_class}",
        ),
        cls="mb-2",
    )

def InitialHeader():
    return Div(
        Div(
            Img(src="images/logo.svg", cls="h-20 w-20 mb-4"),
            H1("GPeter", cls="text-4xl font-bold", style="font-family: 'Playfair Display', serif;"),
            Br(),
            H2("Do more than just study", cls="2xl"),
            cls="flex flex-col items-center justify-center text-center"
        ),

        id="initial-header",
        cls="flex items-center justify-center m-5"
        # Ensure the parent takes full width and height and centers content
    )


def StickyHeader():
    return Div(
        Div(
            Div(
                Img(src="images/logo.svg", cls="h-10 w-10"),  # Smaller logo for sticky header
               # H1("GPeter", cls="text-2xl font-playfair ml-4",style="font-family: 'Playfair Display', serif;"),
                cls="flex flex-col items-center justify-center text-center"
            ),
            cls="max-w-7xl mx-auto flex items-center justify-center"
        ),
        id="sticky-header",
        cls="hidden w-full bg-white text-white py-2 px-6 shadow-md transition-all duration-300 sticky top-0 z-50"
    )




def render_question(question, question_id, topic_id):
    question_text = question["Question"]
    question_type = question["Type"]

    if question_type == "MCQ":
        answers = [question["Answer"]] + question["Distractors"]
        random.shuffle(answers)

        return Div(
            Div(question_text, cls="text-2xl font-bold text-center mb-4"),
            *[
                Button(
                    ans,
                    cls="btn btn-primary w-4/6 my-2 bg-green-200 text-center  text-black ",
                    onclick=f"checkAnswer('{ans}', '{question['Answer']}', '{question_id}_{topic_id}')",
                    id=f"{question_id}_{topic_id}-btn-{index}"
                )
                for index, ans in enumerate(answers)
            ],
            Div(id=f"{question_id}_{topic_id}-feedback", cls="mt-4 text-lg font-bold"),
            Script(f"""
            function checkAnswer(selected, correct, question_id) {{
                var feedback = document.getElementById(question_id + '-feedback');
                if (selected === correct) {{
                    feedback.innerHTML = "Correct!";
                    feedback.classList.add('text-green-500');
                }} else {{
                    feedback.innerHTML = "Incorrect! The correct answer is: " + correct;
                    feedback.classList.add('text-red-500');
                }}
                document.querySelectorAll('#' + question_id + ' button').forEach(btn => btn.disabled = true);
                document.getElementById('next-question-' + question_id).style.display = 'block';
            }}
            """),
            Div(
                Button("Next Question", cls="btn btn-secondary mt-4", id=f"next-question-{question_id}_{topic_id}",
                       hx_post="/next_question", hx_target="#chat-history-container", hx_swap="beforeend", style="display: none;")
            ), cls="flex flex-col items-center justify-center"
        )

    elif question_type == "TrueFalse":
        answers = ["True", "False"]

        return Div(
            Div(question_text, cls="text-2xl font-bold text-center mb-4"),
            *[
                Button(
                    ans,
                    cls="btn btn-primary w-full my-2",
                    onclick=f"checkAnswer('{ans}', '{question['Answer']}', '{question_id}_{topic_id}')",
                    id=f"{question_id}_{topic_id}-btn-{index}"
                )
                for index, ans in enumerate(answers)
            ],
            Div(id=f"{question_id}_{topic_id}-feedback", cls="mt-4 text-lg font-bold"),
            Script(f"""
            function checkAnswer(selected, correct, question_id) {{
                var feedback = document.getElementById(question_id + '-feedback');
                if (selected === correct) {{
                    feedback.innerHTML = "Correct!";
                    feedback.classList.add('text-green-500');
                }} else {{
                    feedback.innerHTML = "Incorrect! The correct answer is: " + correct;
                    feedback.classList.add('text-red-500');
                }}
                document.querySelectorAll('#' + question_id + ' button').forEach(btn => btn.disabled = true);
                document.getElementById('next-question-' + question_id).style.display = 'block';
            }}
            """),
            Div(
                Button("Next Question", cls="btn btn-secondary mt-4", id=f"next-question-{question_id}_{topic_id}",
                       hx_post="/next_question", hx_target="#chat-history-container", hx_swap="beforeend", style="display: none;")
            )
        )


@rt("/next_question", methods=["post"])
async def next_question(request):
    global current_question_index
    current_question_index += 1
    return await display_question()

async def display_question():
    global current_question_index, questions, current_topic_index

    if not questions or current_question_index >= len(questions['Questions']):
        print(f"Error: Questions list is empty or current_question_index ({current_question_index}) is out of range.")
        return await display_slide()  # Move to the next topic's slides if no more questions

    question = questions['Questions'][current_question_index]
    question_id = f"question-{current_question_index}"
    topic_id = f"topic-{current_topic_index}"  # Add a unique identifier for the topic
    print(current_question_index)
    return Div(render_question(question, question_id, topic_id))  # Pass topic_id to render_question


def SlideScript(content_lines, slide_id):
    delay = 500  # Delay between each line in milliseconds
    content_lines_json = json.dumps(content_lines)
    script = f"""
    
    
    
    
    (function() {{
        let contentLines = {content_lines_json};
        let container = $('#slide-content-{slide_id}');
        container.empty();
        let delay = {delay};
        contentLines.forEach((line, index) => {{
            setTimeout(() => {{
                container.append($('<p>').html(line));
                if (index === contentLines.length - 1) {{
                    setTimeout(() => {{
                        $('#next-slide-buttons-{slide_id}').show();
                    }}, delay);
                }}
            }}, delay * index);
        }});
    }})();
    
    """
    return Script(script)



@rt("/")
def get():
    chat_form = Form(
        Input(
            type="text",
            id="user_input",
            name="user_input",
            placeholder="Enter your message...",
            cls="input w-full border-2 border-slate-400",
        ),
        Button("Send", cls="btn btn-primary w-full mt-2"),
        hx_trigger="submit",
        hx_post="/chat",
        hx_target="#chat-history-container",
        hx_swap="beforeend",
        enctype="application/x-www-form-urlencoded",
        cls="mt-4",
    )

    upload_form = Form(
        Input(
            type="file",
            id="upload_file",
            name="upload_file",
            cls="input w-full mt-2",
        ),
        Button("Upload", cls="btn btn-secondary w-full mt-2"),
        onsubmit="uploadFile(event)",
        cls="mt-4",
    )

    chat_history = Div(id="chat-history-container",
                       cls="mt-2 w-11/12 max-w-90vw mx-auto bg-white p-4 rounded-lg overflow-y-auto")

    return Html(
        *headers,
        InitialHeader(),
        StickyHeader(),
        #Titled("GPeter", P("Study any way you want"), style="text-align:center;padding:10px;"),
        chat_history,
        Div(chat_form, cls="w-full max-w-lg mx-auto"),
        Div(upload_form, cls="w-full max-w-lg mx-auto"),
        Script(
            """
            function uploadFile(event) {
                event.preventDefault();
                var formData = new FormData();
                var fileInput = document.getElementById('upload_file');
                formData.append('upload_file', fileInput.files[0]);

                $.ajax({
                    url: '/upload',
                    type: 'POST',
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function(response) {
                        $('#chat-history-container').append(response);
                        fileInput.value = ''; // Clear the input
                    },
                    error: function() {
                        $('#chat-history-container').append('<div class="chat-start"><div class="chat-bubble chat-bubble-secondary">Failed to upload file.</div></div>');
                    }
                });
            }
            
            window.onscroll = function () {
                const initialHeader = document.getElementById("initial-header");
                const stickyHeader = document.getElementById("sticky-header");
                if (window.pageYOffset > 50) {
                    initialHeader.style.display = 'none';
                    stickyHeader.style.display = 'block';
                } else {
                    initialHeader.style.display = 'block';
                    stickyHeader.style.display = 'none';
                }
            };
            """
        ),
    )


@rt("/chat", methods=["post"])
async def chat(request):
    form_data = await request.form()
    user_input = form_data.get("user_input")

    if user_input:
        messages.append((user_input, True))  # Mark as human message
        if sample_file:
            response = model.generate_content(
                [sample_file, f"You are a helpful study bot. Here's the input: {user_input}"])
        else:
            response = model.generate_content([f"You are a helpful study bot. Here's the input: {user_input}"])
        messages.append((response.text, False))  # Mark as AI message

    return Div(
        ChatMessage(user_input, True),
        ChatMessage(response.text, False),
    )


@rt("/upload", methods=["post"])
async def upload(request):
    form_data = await request.form()
    file = form_data.get("upload_file")

    if not file:
        return Div(ChatMessage("No file was uploaded.", False))

    save_folder = "files/"
    os.makedirs(save_folder, exist_ok=True)
    file_path = os.path.join(save_folder, file.filename)

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())

        global sample_file, topics, current_topic_index, current_slide_index, topic_contents
        sample_file = genai.upload_file(path=file_path, display_name=file.filename)
        fileai = genai.get_file(name=sample_file.name)

        topics = createTopics(fileai)
        topic_contents = [None] * len(topics)
        current_topic_index = 0
        current_slide_index = 0

        return Div(
            ChatMessage("File uploaded successfully!", False),
            Div(
                P("Enter study mode for this material?"),
                Button("Yes", cls="btn btn-success", id="yes-btn", hx_post="/start_study_mode",
                       hx_target="#chat-history-container", hx_swap="beforeend", hx_trigger="click"),
                Button("No", cls="btn btn-error", id="no-btn",
                       onclick="document.getElementById('yes-btn').disabled=true; this.disabled=true;"),
                cls="text-center mt-4"
            ),
            Script(
                """
                document.getElementById('yes-btn').onclick = function() {
                    this.disabled = true;
                    document.getElementById('no-btn').disabled = true;
                };
                document.getElementById('no-btn').onclick = function() {
                    this.disabled = true;
                    document.getElementById('yes-btn').disabled = true;
                };
                """
            )
        )

    except Exception as e:
        return Div(ChatMessage("Failed to upload file.", False))


async def display_slide():
    global topics, current_topic_index, current_slide_index, topic_contents, current_question_index, questions

    if current_topic_index < len(topics):
        topic = topics[current_topic_index]

        # Check if the topic content is already generated
        if topic_contents[current_topic_index] is None:
            topic_content = parse_input_string(createContent(sample_file, topic))
            topic_contents[current_topic_index] = topic_content
            qs = createQuestions(sample_file, topic)
            questions = parse_quiz_string(qs)
            print(questions)
            print(qs)
        else:
            topic_content = topic_contents[current_topic_index]

        slides = topic_content.get("Slides", [])

        if current_slide_index < len(slides):
            current_slide = slides[current_slide_index].get("Content", [])

            content = []
            for line in current_slide:
                if "Normal-line" in line:
                    content.append(f"<p>{line.get('Normal-line', '')}</p>")
                elif "Bullet-line" in line:
                    content.append(f"<p>&bull; {line.get('Bullet-line', '')}</p>")
                elif "Numbered-line" in line:
                    content.append(f"<p>{len(content) + 1}. {line.get('Numbered-line', '')}</p>")

            content_lines = [line for line in content]  # Prepare list for JSON serialization

            slide_id = f"slide-{current_topic_index}-{current_slide_index}"

            return Div(
                Slide(topic, content, slide_id),
                SlideScript(content_lines, slide_id),  # Pass the JSON-safe content
                Div(
                    Div(
                        P("Do you want to proceed to the next slide?"),
                        Button("Yes", cls="btn btn-success", id=f"yes-btn-{slide_id}", hx_post="/next_slide",
                               hx_target="#chat-history-container", hx_swap="beforeend", hx_trigger="click"),
                        Button("No", cls="btn btn-error", id=f"no-btn-{slide_id}",
                               onclick=f"document.getElementById('yes-btn-{slide_id}').disabled=true; this.disabled=true;"),
                        cls="text-center mt-4"
                    ),
                    id=f"next-slide-buttons-{slide_id}",
                    style="display: none;"
                ),
                Script(
                    f"""
                    document.getElementById('yes-btn-{slide_id}').onclick = function() {{
                        this.disabled = true;
                        document.getElementById('no-btn-{slide_id}').disabled = true;
                    }};
                    document.getElementById('no-btn-{slide_id}').onclick = function() {{
                        this.disabled = true;
                        document.getElementById('yes-btn-{slide_id}').disabled = true;
                    }};
                    """
                )
            )
        else:
            # Check if all slides are completed, then show the quiz
            if current_question_index < len(questions['Questions']):
                return await display_question()  # Show questions for the topic
            else:
                # Move to the next topic
                current_topic_index += 1
                current_slide_index = 0
                current_question_index = 0  # Reset question index for new topic
                return await display_slide()  # Show the first slide of the next topic
    else:
        return Div(ChatMessage("All topics have been completed. Well done!", False))


@rt("/start_study_mode", methods=["post"])
async def start_study_mode(request):
    global current_topic_index, current_slide_index
    current_topic_index = 0
    current_slide_index = 0
    return await display_slide()


@rt("/next_slide", methods=["post"])
async def next_slide(request):
    global current_slide_index
    current_slide_index += 1
    return await display_slide()


serve()
