$(document).ready(function() {
  var canvas;
  canvas = new fabric.StaticCanvas('my_canvas');
  canvas.backgroundColor = "black";
  return canvas.renderAll();
});