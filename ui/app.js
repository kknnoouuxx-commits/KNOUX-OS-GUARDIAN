(() => {
  const script = document.createElement("script");
  script.type = "module";
  script.src = "assets/js/app.js";
  script.defer = true;
  document.head.appendChild(script);
})();
