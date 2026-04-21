import json
import os

from textual.app import App, ComposeResult
from textual.widgets import Static, Label, Header, Footer, Button, Digits, ProgressBar
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.message import Message

STATS_FILE = "stats.json"


def load_stats() -> int:
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f).get("total_seconds", 0)
    return 0


def save_stats(seconds: int) -> None:
    with open(STATS_FILE, "w") as f:
        json.dump({"total_seconds": seconds}, f)


class TimeDisplay(Digits):
    """Widget to display elapsed time."""

    time_left = reactive(2400)
    total_seconds = 2400
    is_running = reactive(False)

    def on_mount(self) -> None:
        self.update_timer = self.set_interval(1, self.tick, pause=True)

    def tick(self) -> None:
        if self.time_left > 0:
            self.time_left -= 1
            self.post_message(self.TickEvent())
        else:
            self.update_timer.pause()
            self.is_running = False
            self.post_message(self.Finished())

    def watch_time_left(self, time: int) -> None:
        minutes, seconds = divmod(time, 60)
        self.update(f"{minutes:02d}:{seconds:02d}")

    def watch_is_running(self, running: bool) -> None:
        if running:
            self.update_timer.resume()
        else:
            self.update_timer.pause()

    class TickEvent(Message):
        pass

    class Finished(Message):
        pass


class TermidoroApp(App):
    """The timer app."""

    CSS_PATH = "styled.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("left", "switch_mode('study')", "Study mode"),
        ("right", "switch_mode('anime')", "Anime mode"),
        ("space", "toggle_timer", "Play/Pause ⏯"),
        ("r", "reset_timer", "Reset ⟳"),
        ("q", "quit", "Quit"),
    ]

    total_studied = reactive(load_stats())
    current_mode = "study"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="container"):
            yield Label("STUDY (40m)", id="status-label")
            yield TimeDisplay()
            yield ProgressBar(
                total=2400, show_eta=False, show_percentage=True, id="progress-bar"
            )
            yield Static(id="spacer")
            yield Label("", id="total-label")
        yield Footer()

    def on_mount(self) -> None:
        self.update_total_label()

    def on_unmount(self) -> None:
        save_stats(self.total_studied)

    def on_time_display_tick_event(self, event: TimeDisplay.TickEvent) -> None:
        "Update the progress bar every tick"
        timer = self.query_one(TimeDisplay)
        pb = self.query_one("#progress-bar")

        pb.progress = timer.total_seconds - timer.time_left

        if self.current_mode == "study":
            self.total_studied += 1
            if self.total_studied % 10 == 0:
                save_stats(self.total_studied)
            self.update_total_label()

    def update_total_label(self) -> None:
        hours, remainder = divmod(self.total_studied, 3600)
        minutes, _ = divmod(remainder, 60)
        self.query_one("#total-label").update(f"Total Studied: {hours}h {minutes}m")

    def on_time_display_finished(self, event: TimeDisplay.Finished) -> None:
        label = self.query_one("#status-label")
        label.update("TIME IS UP BOI!")

        self.query_one("#container").add_class("finished")

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_switch_mode(self, mode: str) -> None:
        timer = self.query_one(TimeDisplay)
        label = self.query_one("#status-label")
        pb = self.query_one("#progress-bar")

        self.query_one("#container").remove_class("finished")

        timer.is_running = False
        timer.update_timer.pause()
        self.current_mode = mode

        if mode == "study":
            timer.time_left = 2400
            timer.total_seconds = 2400
            pb.update(total=2400)
            label.update("STUDY (40m)")
        elif mode == "anime":
            timer.time_left = 1200
            timer.total_seconds = 1200
            pb.update(total=1200)
            label.update("ANIME (20m)")

    def action_toggle_timer(self) -> None:
        timer = self.query_one(TimeDisplay)
        timer.is_running = not timer.is_running

    def action_reset_timer(self) -> None:
        self.action_switch_mode(self.current_mode)


def main() -> None:
    app = TermidoroApp()
    app.run()


if __name__ == "__main__":
    main()
