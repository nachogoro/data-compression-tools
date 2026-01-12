import tkinter as tk
from tkinter import simpledialog, messagebox
import math
import heapq
import itertools


# A simple Huffman node for building the tree.
class HuffmanNode:
    def __init__(self, char, freq, left=None, right=None):
        self.char = char  # Character (or '*' for internal nodes)
        self.freq = freq  # Frequency
        self.left = left  # Left child
        self.right = right  # Right child


# A class that associates a HuffmanNode with its visual representation.
class VisualNode:
    def __init__(self, huff_node, x, y):
        self.huff_node = huff_node  # The underlying Huffman node.
        self.x = x  # x-coordinate (center)
        self.y = y  # y-coordinate (center)
        self.circle_id = None  # Canvas id for the circle.
        self.text_id = None  # Canvas id for the label.
        self.children = []  # List of child VisualNodes (if merged)
        # Each entry: (line_id, child, label_id) – now label_id will be None.
        self.lines = []


class HuffmanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Huffman Encoding Visualizer")

        # Top frame: input text, control buttons, checkbox, and speed slider.
        top_frame = tk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        tk.Label(top_frame, text="Input String:").pack(side=tk.LEFT)
        self.input_entry = tk.Entry(top_frame, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=5)
        self.input_entry.insert(0, "AAAABBBCCDDEE")  # default example

        self.start_button = tk.Button(top_frame, text="Start", command=self.start_process)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.next_button = tk.Button(top_frame, text="Next Step", command=self.next_step,
                                     state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)
        self.play_button = tk.Button(top_frame, text="Play", command=self.play_process,
                                     state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = tk.Button(top_frame, text="Pause", command=self.pause_process,
                                      state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.minimize_var = tk.IntVar(value=0)
        self.minimize_checkbox = tk.Checkbutton(top_frame, text="Minimize rearrangements",
                                                variable=self.minimize_var)
        self.minimize_checkbox.pack(side=tk.LEFT, padx=5)

        self.speed_scale = tk.Scale(top_frame, from_=1.0, to=3.0, resolution=0.1,
                                    orient=tk.HORIZONTAL, label="Speed (x)")
        self.speed_scale.set(1.0)
        self.speed_scale.pack(side=tk.LEFT, padx=5)

        # Create a horizontal PanedWindow so that the right panel is adjustable.
        self.paned = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left pane: the canvas.
        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas = tk.Canvas(self.paned, width=self.canvas_width, height=self.canvas_height,
                                bg="white")
        self.paned.add(self.canvas)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # Right pane: the result panel.
        self.result_panel = tk.Frame(self.paned, bg="lightgrey", relief=tk.SUNKEN, borderwidth=2)
        tk.Label(self.result_panel, text="Huffman Codes & Stats", bg="lightgrey",
                 font=("Arial", 12, "bold")).pack(anchor=tk.N, pady=5)
        self.result_text = tk.Text(self.result_panel, width=40, height=30)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.result_text.config(state=tk.DISABLED)
        self.paned.add(self.result_panel)

        # Parameters and state.
        self.node_radius = 20  # radius for node circles.
        self.vertical_gap = 80  # vertical gap between levels.
        self.leaf_margin = None  # horizontal gap between leaf centers (set in start_process).
        self.animation_running = False
        self.active_nodes = []  # List of current subtree roots.
        self.last_merge_children = []  # Stores the two nodes last merged.
        self.frequency_distribution = {}  # symbol: frequency

        # Graph bounding box values (computed at start and fixed thereafter)
        self.graph_bbox_left = None
        self.graph_bbox_right = None
        self.graph_bbox_top = None
        self.graph_bbox_bottom = None
        self.graph_bbox_center = None

        self.playing = False  # Auto-play mode flag.

    def start_process(self):
        """Reset and start a new Huffman tree process."""
        self.canvas.delete("all")
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.active_nodes = []
        self.frequency_distribution = {}
        self.playing = False

        text = self.input_entry.get().strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter a non-empty string.")
            return

        # Compute frequency distribution.
        freq = {}
        total = len(text)
        for ch in text:
            freq[ch] = freq.get(ch, 0) + 1
        self.frequency_distribution = freq

        # Sort characters in decreasing order of frequency.
        sorted_items = sorted(freq.items(), key=lambda item: item[1], reverse=True)
        num = len(sorted_items)
        spacing = self.canvas_width / (num + 1)
        self.leaf_margin = spacing - 2 * self.node_radius

        leaf_y = self.canvas_height - 50
        for i, (ch, f) in enumerate(sorted_items):
            x = spacing * (i + 1)
            node = VisualNode(HuffmanNode(ch, f), x, leaf_y)
            self.draw_node(node)
            self.active_nodes.append(node)

        # Precompute the fixed graph bounding box.
        self.graph_bbox_left = min(node.x - self.node_radius for node in self.active_nodes)
        self.graph_bbox_right = max(node.x + self.node_radius for node in self.active_nodes)
        final_tree = self.compute_final_tree()
        max_level = self.compute_max_level(final_tree)
        graph_height = (max_level * self.vertical_gap) + 2 * self.node_radius
        self.graph_bbox_bottom = leaf_y + self.node_radius
        self.graph_bbox_top = self.graph_bbox_bottom - graph_height
        self.graph_bbox_center = ((self.graph_bbox_left + self.graph_bbox_right) / 2,
                                  (self.graph_bbox_top + self.graph_bbox_bottom) / 2)
        self.center_graph()

        self.next_button.config(state=tk.NORMAL)
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)

    def draw_node(self, node, radius=None):
        """Draw a node (circle with text) on the canvas."""
        if radius is None:
            radius = self.node_radius
        x, y = node.x, node.y
        node.circle_id = self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                                 fill="lightblue", outline="black")
        text = f"{node.huff_node.char}\n{node.huff_node.freq}"
        node.text_id = self.canvas.create_text(x, y, text=text)

    def get_subtree_nodes(self, node):
        """Recursively collect all VisualNodes in the subtree rooted at node."""
        nodes = [node]
        for child in node.children:
            nodes.extend(self.get_subtree_nodes(child))
        return nodes

    def get_subtree_bbox(self, node):
        """Return (min_x, max_x) for all nodes in the subtree rooted at node, considering node radii."""
        nodes = self.get_subtree_nodes(node)
        min_x = min(n.x - self.node_radius for n in nodes)
        max_x = max(n.x + self.node_radius for n in nodes)
        return (min_x, max_x)

    def update_node_position(self, node):
        """Update the canvas coordinates for a node’s circle, text, and its connecting line labels."""
        self.canvas.coords(node.circle_id,
                           node.x - self.node_radius, node.y - self.node_radius,
                           node.x + self.node_radius, node.y + self.node_radius)
        self.canvas.coords(node.text_id, node.x, node.y)
        for (line_id, child, label_id) in node.lines:
            self.canvas.coords(line_id,
                               node.x, node.y + self.node_radius,
                               child.x, child.y - self.node_radius)
            # If label exists, update its position.
            if label_id is not None:
                mid_x = (node.x + child.x) / 2
                mid_y = (node.y + child.y) / 2
                self.canvas.coords(label_id, mid_x, mid_y)

    def compute_final_tree(self):
        """Compute the final Huffman tree using a greedy algorithm (for final height)."""
        counter = itertools.count()
        heap = []
        for ch, f in self.frequency_distribution.items():
            heapq.heappush(heap, (f, next(counter), HuffmanNode(ch, f)))
        while len(heap) > 1:
            f1, _, node1 = heapq.heappop(heap)
            f2, _, node2 = heapq.heappop(heap)
            new_node = HuffmanNode('*', f1 + f2, left=node1, right=node2)
            heapq.heappush(heap, (f1 + f2, next(counter), new_node))
        return heap[0][2]

    def compute_max_level(self, node, level=0):
        """Compute the maximum level (depth) of the Huffman tree."""
        if node.left is None and node.right is None:
            return level
        return max(self.compute_max_level(node.left, level + 1),
                   self.compute_max_level(node.right, level + 1))

    def get_all_nodes(self):
        """Collect all nodes from all active trees."""
        nodes = []
        for node in self.active_nodes:
            nodes.extend(self.get_subtree_nodes(node))
        return nodes

    def center_graph(self):
        """
        Shift all nodes so that the fixed graph bounding box is centered in the current canvas.
        (The bounding box is computed at start and remains fixed.)
        """
        if self.graph_bbox_center is None:
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        new_center = (cw / 2, ch / 2)
        offset_x = new_center[0] - self.graph_bbox_center[0]
        offset_y = new_center[1] - self.graph_bbox_center[1]
        for node in self.get_all_nodes():
            node.x += offset_x
            node.y += offset_y
            self.update_node_position(node)
        self.graph_bbox_center = (self.graph_bbox_center[0] + offset_x,
                                  self.graph_bbox_center[1] + offset_y)

    def on_canvas_resize(self, event):
        """When the canvas is resized, re-center the graph."""
        self.canvas_width = event.width
        self.canvas_height = event.height
        self.center_graph()

    def rearrange_nodes(self, callback):
        """
        Reorder active nodes (and their entire subtrees) in decreasing order of frequency,
        and animate their horizontal movement so that:
          - The leftmost active tree’s bounding box stays at the same x.
          - Each subsequent tree’s bounding box is positioned exactly self.leaf_margin pixels
            to the right of the previous tree's bounding box.
        This preserves the overall spacing between leaf nodes.
        """
        old_order = sorted(self.active_nodes, key=lambda node: self.get_subtree_bbox(node)[0])
        if not old_order:
            callback()
            return
        overall_left = self.get_subtree_bbox(old_order[0])[0]

        new_order = sorted(self.active_nodes, key=lambda node: node.huff_node.freq, reverse=True)
        bbox_widths = {}
        for node in new_order:
            L, R = self.get_subtree_bbox(node)
            bbox_widths[node] = R - L
        target_centers = {}
        if new_order:
            first = new_order[0]
            first_width = bbox_widths[first]
            target_left = overall_left
            target_centers[first] = target_left + first_width / 2
            prev_right = target_left + first_width
            for node in new_order[1:]:
                width = bbox_widths[node]
                new_left = prev_right + self.leaf_margin
                target_centers[node] = new_left + width / 2
                prev_right = new_left + width

        anim_data = []
        for node in new_order:
            L, R = self.get_subtree_bbox(node)
            current_center = (L + R) / 2
            subtree = self.get_subtree_nodes(node)
            init_positions = {n: n.x for n in subtree}
            anim_data.append((node, current_center, target_centers[node], init_positions))

        steps = 20
        step_time = int(20 / self.speed_scale.get())

        def animate_step(i):
            if i > steps:
                for node, init_center, target_center, init_pos in anim_data:
                    offset = target_center - init_center
                    for subnode in self.get_subtree_nodes(node):
                        subnode.x = init_pos[subnode] + offset
                        self.update_node_position(subnode)
                callback()
                return
            fraction = i / steps
            for node, init_center, target_center, init_pos in anim_data:
                offset = (target_center - init_center) * fraction
                for subnode in self.get_subtree_nodes(node):
                    new_x = init_pos[subnode] + offset
                    subnode.x = new_x
                    self.update_node_position(subnode)
            self.root.after(step_time, lambda: animate_step(i + 1))

        animate_step(0)

    def select_pair_minimize(self, sorted_nodes):
        """
        Return indices (i, i+1) for a pair of adjacent nodes (sorted by x) that can be merged under
        Huffman rules, or None if none exist.
        """
        if len(sorted_nodes) < 2:
            return None
        overall_sorted = sorted(sorted_nodes, key=lambda n: n.huff_node.freq)
        candidate_sum = overall_sorted[0].huff_node.freq + overall_sorted[1].huff_node.freq
        candidates = []
        for i in range(len(sorted_nodes) - 1):
            if sorted_nodes[i].huff_node.freq + sorted_nodes[i + 1].huff_node.freq == candidate_sum:
                candidates.append((i, i + 1))
        if candidates:
            return candidates[-1]
        return None

    def next_step(self):
        """Proceed to the next merge step. When finished, show results."""
        if self.animation_running:
            return
        if len(self.active_nodes) <= 1:
            final_tree = self.active_nodes[0].huff_node
            codes = self.generate_codes(final_tree)
            self.update_results(codes)
            self.playing = False
            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            return
        if self.minimize_var.get() == 1:
            sorted_nodes = sorted(self.active_nodes, key=lambda n: n.x)
            pair = self.select_pair_minimize(sorted_nodes)
            if pair is not None:
                node1 = sorted_nodes[pair[0]]
                node2 = sorted_nodes[pair[1]]
                self.active_nodes.remove(node1)
                self.active_nodes.remove(node2)
                self.highlight_nodes([node1, node2], "orange",
                                     lambda: self.merge_nodes(node1, node2))
                return
        self.rearrange_nodes(lambda: self.merge_smallest_nodes())

    def merge_smallest_nodes(self):
        """Merge the two rightmost active nodes (by x-coordinate)."""
        if len(self.active_nodes) < 2:
            self.animation_running = False
            return
        sorted_nodes = sorted(self.active_nodes, key=lambda n: n.x)
        node1 = sorted_nodes[-2]
        node2 = sorted_nodes[-1]
        self.active_nodes.remove(node1)
        self.active_nodes.remove(node2)
        self.highlight_nodes([node1, node2], "orange", lambda: self.merge_nodes(node1, node2))

    def highlight_nodes(self, nodes, color, callback):
        """Highlight given nodes by changing their fill color, then call callback."""
        for node in nodes:
            self.canvas.itemconfig(node.circle_id, fill=color)
        self.root.after(500, callback)

    def merge_nodes(self, node1, node2):
        """Merge two nodes, create their parent, and animate its appearance."""
        self.canvas.itemconfig(node1.circle_id, fill="lightblue")
        self.canvas.itemconfig(node2.circle_id, fill="lightblue")
        combined_freq = node1.huff_node.freq + node2.huff_node.freq
        parent_huff = HuffmanNode('*', combined_freq, left=node1.huff_node, right=node2.huff_node)
        new_x = (node1.x + node2.x) / 2
        new_y = min(node1.y, node2.y) - self.vertical_gap
        new_visual = VisualNode(parent_huff, new_x, new_y)
        new_visual.children = [node1, node2]
        self.animate_node_creation(new_visual, lambda: self.finish_merge(new_visual))

    def animate_node_creation(self, node, callback, steps=10):
        """Animate a node’s appearance by scaling its circle from 0 to full size."""
        x, y = node.x, node.y
        initial_radius = 0
        final_radius = self.node_radius
        node.circle_id = self.canvas.create_oval(x, y, x, y,
                                                 fill="lightblue", outline="black")
        node.text_id = self.canvas.create_text(x, y,
                                               text=f"{node.huff_node.char}\n{node.huff_node.freq}")

        def step(i):
            if i > steps:
                callback()
                return
            r = initial_radius + (final_radius - initial_radius) * i / steps
            self.canvas.coords(node.circle_id, x - r, y - r, x + r, y + r)
            self.root.after(50, lambda: step(i + 1))

        step(0)

    def finish_merge(self, new_visual):
        """After parent node animation, draw connecting lines (without extra labels) and update active nodes."""
        line_ids = []
        for child in new_visual.children:
            line_id = self.canvas.create_line(new_visual.x, new_visual.y + self.node_radius,
                                              child.x, child.y - self.node_radius, width=2)
            # No labels on the branches.
            line_ids.append((line_id, child, None))
        new_visual.lines = line_ids
        self.active_nodes.append(new_visual)
        self.active_nodes.sort(key=lambda n: n.huff_node.freq, reverse=True)
        self.animation_running = False
        if self.playing:
            self.root.after(100, self.next_step)

    def play_process(self):
        """Start auto-play mode (simulate next_step repeatedly)."""
        if not self.playing:
            self.playing = True
            self.play_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.next_step()

    def pause_process(self):
        """Pause auto-play mode."""
        if self.playing:
            self.playing = False
            self.play_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)

    def next_step(self):
        """Proceed to the next merge step. When finished, show results."""
        if self.animation_running:
            return
        if len(self.active_nodes) <= 1:
            final_tree = self.active_nodes[0].huff_node
            codes = self.generate_codes(final_tree)
            self.update_results(codes)
            self.playing = False
            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            return
        if self.minimize_var.get() == 1:
            sorted_nodes = sorted(self.active_nodes, key=lambda n: n.x)
            pair = self.select_pair_minimize(sorted_nodes)
            if pair is not None:
                node1 = sorted_nodes[pair[0]]
                node2 = sorted_nodes[pair[1]]
                self.active_nodes.remove(node1)
                self.active_nodes.remove(node2)
                self.highlight_nodes([node1, node2], "orange",
                                     lambda: self.merge_nodes(node1, node2))
                return
        self.rearrange_nodes(lambda: self.merge_smallest_nodes())

    def select_pair_minimize(self, sorted_nodes):
        """Return indices (i, i+1) for a pair of adjacent nodes (sorted by x) that can be merged under Huffman rules, or None."""
        if len(sorted_nodes) < 2:
            return None
        overall_sorted = sorted(sorted_nodes, key=lambda n: n.huff_node.freq)
        candidate_sum = overall_sorted[0].huff_node.freq + overall_sorted[1].huff_node.freq
        candidates = []
        for i in range(len(sorted_nodes) - 1):
            if sorted_nodes[i].huff_node.freq + sorted_nodes[i + 1].huff_node.freq == candidate_sum:
                candidates.append((i, i + 1))
        if candidates:
            return candidates[-1]
        return None

    def play_process(self):
        """Start auto-play mode."""
        if not self.playing:
            self.playing = True
            self.play_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.next_step()

    def pause_process(self):
        """Pause auto-play mode."""
        if self.playing:
            self.playing = False
            self.play_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)

    def generate_codes(self, node, prefix="", code_dict=None):
        """Recursively traverse the Huffman tree to generate codes."""
        if code_dict is None:
            code_dict = {}
        if node.left is None and node.right is None:
            code_dict[node.char] = prefix or "0"
        else:
            if node.left:
                self.generate_codes(node.left, prefix + "0", code_dict)
            if node.right:
                self.generate_codes(node.right, prefix + "1", code_dict)
        return code_dict

    def update_results(self, codes):
        """Update the result panel with a table of symbols, frequencies, codes, code lengths,
           plus the entropy and average code length.
        """
        total = sum(self.frequency_distribution.values())
        lines = []
        header = f"{'Symbol':^8} | {'Freq':^8} | {'Code':^12} | {'Len':^5}"
        separator = "-" * len(header)
        lines.append(header)
        lines.append(separator)
        avg_length = 0.0
        entropy = 0.0
        for symbol in sorted(self.frequency_distribution.keys()):
            freq = self.frequency_distribution[symbol]
            p = freq / total
            code = codes.get(symbol, "")
            length = len(code)
            avg_length += p * length
            if p > 0:
                entropy -= p * math.log2(p)
            freq_str = f"{freq}/{total}"
            lines.append(f"{symbol:^8} | {freq_str:^8} | {code:^12} | {length:^5}")
        lines.append(separator)
        lines.append(f"Entropy: {entropy:.4f} bits/symbol")
        lines.append(f"Avg code length: {avg_length:.4f} bits/symbol")
        result_str = "\n".join(lines)
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_str)
        self.result_text.config(state=tk.DISABLED)

    def solve_process(self):
        """For compatibility, 'Solve' just starts auto-play."""
        self.play_process()


def main():
    root = tk.Tk()
    app = HuffmanGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
