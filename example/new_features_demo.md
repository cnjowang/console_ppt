<!-- showprogress: true -->

<title>New Features Demo</title>
<subtitle>Testing Local Animation & Progress Control</subtitle>

---

# Local Animation: Move

<animate type="move" range="3" speed="1.5">
  <div align="center">
    <h1>I am moving left and right!</h1>
    <p>Range is set to 3</p>
  </div>
</animate>

<animate type="move" range="1" speed="0.5">
  <p>I am moving slowly with range 1</p>
</animate>

---

# Global Progress Control

This presentation has `showprogress: true` in the header.
The progress bar should be visible on this slide.

---

<!-- hideprogress -->

# Hidden Progress

This slide has `<!-- hideprogress -->`.
The progress bar should be hidden even though global is true.

---

# Global Progress Test (Part 2)

Now let's test if setting `showprogress: false` works.
(I will create another file for that or just change this one later).

Actually, I'll create `example/hide_global_progress_demo.md`.
