var updating = false;

function updatePixel() {
   var pixel = $(".pixel").attr("id");
   var r = $("#r").val(), g = $("#g").val(), b = $("#b").val();

   updating = true;
   $.post("/pixel/" + pixel, { r: r, g: g, b: b, immediate: "false" })
      .always(function () {
         updating = false;

         if (r != $("#r").val() ||
             g != $("#g").val() ||
             b != $("#b").val()) {
            updatePixel();
         }
      });
}

function updateRgbFromHsl() {
   var $r = $("#r"), $g = $("#g"), $b = $("#b"), $h = $("#h"), $s = $("#s"), $l = $("#l");
   var h = $h.val(), s = $s.val() / 100, l = $l.val() / 100;

   var c = (1 - Math.abs(2 * l - 1)) * s;
   var hp = h / 60;
   var x = c * (1 - Math.abs(hp % 2 - 1));
   var m = l - c / 2;

   var r, g, b;
   if (hp < 1) {
      r = c + m; g = x + m; b = m;
   } else if (hp < 2) {
      r = x + m, g = c + m; b = m;
   } else if (hp < 3) {
      r = m; g = c + m; b = x + m;
   } else if (hp < 4) {
      r = m, g = x + m; b = c + m;
   } else if (hp < 5) {
      r = x + m; g = m; b = c + m;
   } else {
      r = c + m; g = m; b = x + m;
   }

   $r.val(r * 255); $g.val(g * 255); $b.val(b * 255);
   console.log(h + ", " + s + ", " + l + " -> " + r + ", " + g + ", " + b);
}

function updateHslFromRgb() {
   var $r = $("#r"), $g = $("#g"), $b = $("#b"), $h = $("#h"), $s = $("#s"), $l = $("#l");
   var r = $r.val() / 255, g = $g.val() / 255, b = $b.val() / 255;

   var max = Math.max(r, g, b), min = Math.min(r, g, b);
   var h, s, l = (max + min) / 2;

   if (max == min){
      h = s = 0; // achromatic
   } else {
      var d = max - min;

      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

      switch(max){
         case r: h = (g - b) / d + (g < b ? 6 : 0); break;
         case g: h = (b - r) / d + 2; break;
         case b: h = (r - g) / d + 4; break;
      }

      h /= 6;
   }

   $h.val(h * 360); $s.val(s * 100); $l.val(l * 100);
}

function updatePreviews() {
   var $r = $("#r"), $g = $("#g"), $b = $("#b"), $h = $("#h"), $s = $("#s"), $l = $("#l");
   var r = $r.val(), g = $g.val(), b = $b.val(), h = $h.val(), s = $s.val(), l = $l.val();

   $("#preview").css("background", "rgb(" + r + ", " + g + ", " + b + ")");
   $r.css('background', "linear-gradient(to right, rgb(0, " + g + ", " + b + "), rgb(255, " + g + ", " + b + "))");
   $g.css('background', "linear-gradient(to right, rgb(" + r + ", 0, " + b + "), rgb(" + r + ", 255, " + b + "))");
   $b.css('background', "linear-gradient(to right, rgb(" + r + ", " + g + ", 0), rgb(" + r + ", " + g + ", 255))");
   $h.css("background", "linear-gradient(to right, hsl(0, " + s + "%, " + l + "%), hsl(60, " + s + "%, " + l + "%), hsl(120, " + s + "%, " + l + "%), hsl(180, " + s + "%, " + l + "%), hsl(240, " + s + "%, " + l + "%), hsl(300, " + s + "%, " + l + "%), hsl(360, " + s + "%, " + l + "%))");
   $s.css("background", "linear-gradient(to right, hsl(" + h + ", 0%, " + l + "%), hsl(" + h + ", 100%, " + l + "%))");
   $l.css("background", "linear-gradient(to right, hsl(" + h + ", " + s + "%, 0%), hsl(" + h + ", " + s + "%, 100%))");
}

$( document ).ready(function () {
   $(".rgb").change(function () {
      var input = $( this );

      if (input.data('updating')) {
         console.log("Waiting...\n");
         return;
      }

      updateColor(input);
   });

   $(".preset-btn").click(function () {
      var preset = $( this );

      $.post("/preset/apply", { preset: preset.attr('id') })
         .always(function () {
            $(".preset-btn").removeClass("active");
            preset.addClass("active");
         });
   });

   $(".preset-save-btn").click(function () {
      var name = prompt("Preset name:");

      if (name != null) {
         $.post("/preset/save", { name: name });
      }
   });

   $(".preset-remove-btn").click(function () {
      var name = $( this ).parent().attr("id");

      if (confirm("Are you sure you want to delete \"" + name + "\"?")) {
         $.post("/preset/delete", { name: name });
      }
   });

   $("#r, #g, #b").change(function () {
      updateHslFromRgb();
      updatePreviews();
      updatePixel();
   });

   $("#h, #s, #l").change(function () {
      updateRgbFromHsl();
      updatePreviews();
      updatePixel();
   });

   updateHslFromRgb();
   updatePreviews();
});
