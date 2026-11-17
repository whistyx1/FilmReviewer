# Film Reviewer

A desktop app for writing film reviews on macOS and Windows. Film Reviewer combines eight whole-number ratings into a score out of 100, then formats the result with your notes. You can copy the review as text or an image and save it to local history. The interface uses matte black and lime green.

## What you can do

1. Search for a film with TMDB to fill in its title, year, director, and poster, or enter the details yourself.
2. Rate eight aspects from 1 to 10. The **?** beside each metric explains what it means, and the calculation stays visible under the sliders.
3. Write optional notes. **Basic cleanup** fixes spacing and simple punctuation locally; **Brush up with Ollama** rewrites them with a local AI model. After a rewrite, **Try another version** asks for different wording. Your original notes remain available.
4. Check the review preview, then **Copy text**, **Copy image**, or **Save review**. Open **History** to search, reopen, update, or delete saved reviews.

## How the rating works

The first five metrics—story and characters, acting, visuals, pacing, and sound—contribute up to **40 points** together. Their 1–10 ratings are averaged, scaled to 40, and rounded to a whole number.

The last three contribute up to **60 points**: enjoyment is multiplied by 3, emotional impact by 2, and lasting impression by 1. The two parts are added for the final score out of 100. For example, first-group ratings of `8 + 8 + 9 + 7 + 8` give `32/40`; subjective ratings of `9, 8, 8` give `(9 × 3) + (8 × 2) + 8 = 51/60`, for **83/100**.

## Project structure

| Path | Role |
| --- | --- |
| [`main.py`](main.py), [`film_reviewer/app.py`](film_reviewer/app.py) | Start the Qt application and apply its shared style. |
| [`film_reviewer/ui/`](film_reviewer/ui/) | Main window, rating controls, history dialog, background, and theme. |
| [`film_reviewer/models/`](film_reviewer/models/) | Movie and saved-review data, rating calculation, and review text formatting. |
| [`film_reviewer/services/`](film_reviewer/services/) | TMDB search and posters, local Ollama requests, and review history storage. |
| `launch_*.command` / `launch_*.bat` | Run from source after setting up the local Python environment. |
| `build_*.command` / `build_*.bat` | Create a standalone app with PyInstaller on the current operating system. |

The UI coordinates the workflow. The rating and formatting code lives in `models`, while network and disk access lives in `services`. TMDB and Ollama requests run without blocking the window. Saved reviews are JSON snapshots written atomically to the operating system's app data folder; each snapshot includes the film details, ratings, original and brushed-up notes, and poster.

## Open from the project folder

Install [Python 3.12](https://www.python.org/downloads/) once on each computer. On Windows, enable **Add Python to PATH** during installation.

- **Mac:** Double-click `launch_mac.command`.
- **Windows:** Double-click `launch_windows.bat`.

The first launch creates a local `.venv` and installs the Python dependencies. It needs an internet connection. Later launches use the same environment.

To use the project on a second computer, copy the project folder there or download it from GitHub after the source has been pushed. Do not copy `.venv` between computers; each launcher creates the environment needed for its own operating system.

For a desktop shortcut, make an alias of `launch_mac.command` on Mac, or right-click `launch_windows.bat` on Windows and choose **Send to → Desktop (create shortcut)**. Keep the project folder in place so the shortcut can find it.

## Build a standalone app

Run the build script **on the computer that will use the result**:

- **Mac:** Double-click `build_mac.command`. Open `dist/FilmReviewer.app`; you can move it to Applications or the Desktop.
- **Windows:** Double-click `build_windows.bat`. After a successful build it opens `dist\FilmReviewer\FilmReviewer.exe` automatically. Keep the whole `FilmReviewer` folder together; create a desktop shortcut to the `.exe` if you like.

The build scripts install PyInstaller and package Python with the app. A Mac build cannot create a Windows executable, and a Windows build cannot create a Mac app. The `dist` and `build` folders are local build output and are not part of the source repository.

## Optional services and saved data

- **TMDB:** Click **Connect TMDB** in the app and paste your own API Read Access Token to search films and load posters. You only need to do this once per computer. Developers can also set `TMDB_READ_ACCESS_TOKEN` in the environment.
- **Ollama:** Install Ollama on each computer where you want **Brush up with Ollama**. Download a model with `ollama pull gemma3:1b` (or another model). If its local server is stopped, Film Reviewer tries to start it when you brush up a review. Review notes are sent to Ollama on `127.0.0.1:11434`; **Basic cleanup** works without it.
- **History and settings:** Click **Save review** to keep a review. History is stored as `reviews.json` in the system's application data directory, while the TMDB token and selected Ollama model use Qt settings. These stay on each computer separately; copying the project or app does not transfer them.
