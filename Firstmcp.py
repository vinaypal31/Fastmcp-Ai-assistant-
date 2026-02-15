from fastmcp import FastMCP
from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv
load_dotenv()
import smtplib
from email.message import EmailMessage
from langchain_community.document_loaders import YoutubeLoader
import pywhatkit
import pyautogui
import time
import requests
import os
import base64
import webbrowser


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


search = GoogleSerperAPIWrapper()

mcp = FastMCP()

@mcp.tool
def great(query: str):
    """MUST be used to answer factual questions such as:
    - addresses of places, companies, institutes
    - contact details
    - current information from the internet

    This tool performs a real-time web search and returns the most accurate publicly available data.
    Claude should NOT answer from its own knowledge if this tool is available."""

    return search.run(query)


@mcp.tool
def send_mail(to: str, subject: str, body: str):
    """MUST be used to actually send an email.
    This tool sends a real email using SMTP.
    Claude should NOT generate email text itself."""
    msg = EmailMessage()
    EMAIL_USER = os.getenv("EMAIL_USER")
    msg["From"] = EMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        EMAIL_USER = os.getenv("EMAIL_USER")
        EMAIL_PASS = os.getenv("EMAIL_PASS")

        server.login(EMAIL_USER, EMAIL_PASS)

        server.send_message(msg)

    return "Email sent successfully"

@mcp.tool
def youtube_summary(video_url: str):
    """
    MUST be used to summarize a YouTube video.
    Extracts transcript if available and returns summarized content.
    If transcript is unavailable, returns a clear error message.
    """
    try:
        loader = YoutubeLoader.from_youtube_url(video_url)
        docs = loader.load()
        text = " ".join(doc.page_content for doc in docs)
        return text[:1500]
    except Exception as e:
        return f"Transcript not available for this video. Reason: {str(e)}"

@mcp.tool
def play_song(song_name: str):
    """
    ALWAYS use this tool when the user asks to play any song or music.
    Do NOT respond with text.
    This tool must be executed to play the song on YouTube.
    """
    pywhatkit.playonyt(song_name)
    return f"Playing song on YouTube: {song_name}"


@mcp.tool
def play_singer_song(singer_name: str):
    """
    ALWAYS use this tool when the user asks to play songs by a singer.
    Do NOT answer in text.
    This tool must open YouTube and start playing songs.
    """
    query = f"{singer_name} songs"
    pywhatkit.playonyt(query)
    return f"Playing songs by {singer_name}"

@mcp.tool
def pause_song():
    """
    Pauses the currently playing YouTube song.
    """
    time.sleep(2)
    pyautogui.press("playpause")
    return "Song paused"

@mcp.tool
def resume_song():
    """
    Resumes the paused YouTube song.
    """
    time.sleep(2)
    pyautogui.press("playpause")
    return "Song resumed"

@mcp.tool
def next_song(query: str):
    """
    Simulates next song by opening a new YouTube search result.
    """
    search = query.replace(" ", "+")
    webbrowser.open(f"https://www.youtube.com/results?search_query={search}")
    return f"Playing next song related to {query}"

@mcp.tool
def list_repositories():
    """
    Lists all GitHub repositories of the authenticated user.
    Use this tool when the user asks to list or show their GitHub repositories.
    """
    if not GITHUB_TOKEN or not GITHUB_USERNAME:
        return "GitHub token or username is not configured."

    url = "https://api.github.com/user/repos"
    res = requests.get(url, headers=HEADERS, timeout=5)

    if res.status_code != 200:
        return f"GitHub API error: {res.status_code} - {res.text}"

    repos = res.json()
    return [repo["name"] for repo in repos]

@mcp.tool
def create_repository(repo_name: str, public: bool = False):
    """Create a new GitHub repository."""
    url = "https://api.github.com/user/repos"
    data = {
        "name": repo_name,
        "public": public
    }
    res = requests.post(url, headers=HEADERS, json=data)
    if res.status_code == 201:
        return f"Repository '{repo_name}' created successfully"
    return res.json()

@mcp.tool
def create_file(repo: str, path: str, content: str, message: str):
    """Create a file in a GitHub repository and commit it."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo}/contents/{path}"

    encoded_content = base64.b64encode(content.encode()).decode()

    data = {
        "message": message,
        "content": encoded_content
    }

    res = requests.put(url, headers=HEADERS, json=data)

    if res.status_code in [200, 201]:
        return f"File '{path}' committed to repo '{repo}'"
    return res.json()

@mcp.tool
def read_file(repo: str, path: str):
    """Read a file from a GitHub repository."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo}/contents/{path}"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    content = base64.b64decode(data["content"]).decode()
    return content


@mcp.tool
def open_website(url : str):
    """Open a website in the default browser"""
    webbrowser.open(url)
    return f"Opening {url}"


@mcp.tool
def take_screenshot():
    """Take screenshot after 5 second delay and save it"""
    time.sleep(5)

    file_path = os.path.abspath("screenshot.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(file_path)

    return f"Screenshot saved at {file_path}"


@mcp.tool
def vol_up():
    """Increases system volume"""
    pyautogui.press("volumeup")
    return "Volume Increases"

@mcp.tool
def vol_down():
    """Decreases system volume"""
    pyautogui.press("volumedown")
    return "Volume down"



if __name__ == "__main__":
    mcp.run()