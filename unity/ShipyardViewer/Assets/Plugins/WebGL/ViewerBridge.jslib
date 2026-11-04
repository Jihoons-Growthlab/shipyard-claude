// Unity -> browser. See contracts/unity-viewer.md.
mergeInto(LibraryManager.library, {
  ShipViewer_NotifyReady: function () {
    var canvas = Module.canvas;
    if (canvas) canvas.dispatchEvent(new CustomEvent('shipviewer-ready'));
  },
});
