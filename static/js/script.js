function updateColor(input) {
   var value = input.val();

   console.log("Updating to " + value + ".\n");

   input.data('updating', true);
   $.post("/pixel/" + input.attr('id'), { color: value, immediate: "false" })
      .always(function () {
         input.data('updating', false);

         var next_value = input.val();
         if (next_value !== value) {
            console.log("Updating to " + next_value + " after POST.\n");
            updateColor(input);
         }
      });
}

function updateRgbFromHsv() {
}

function updateHsvFromRgb() {
}

function updatePreviews() {
   var $r = $("#r"), $g = $("#g"), $b = $("#b"), $h = $("#h"), $s = $("#s"), $v = $("#v");
   var r = $r.val(), g = $g.val(), b = $b.val(), h = $h.val(), s = $s.val(), v = $v.val();

   $("#preview").css("background", "rgb(" + r + ", " + g + ", " + b + ")");
   $r.css('background', "linear-gradient(to right, rgb(0, " + g + ", " + b + "), rgb(255, " + g + ", " + b + "))");
   $g.css('background', "linear-gradient(to right, rgb(" + r + ", 0, " + b + "), rgb(" + r + ", 255, " + b + "))");
   $b.css('background', "linear-gradient(to right, rgb(" + r + ", " + g + ", 0), rgb(" + r + ", " + g + ", 255))");
   $h.css("background", "linear-gradient(to right, hsl(0, " + s + "%, " + v + "%), hsl(60, " + s + "%, " + v + "%), hsl(120, " + s + "%, " + v + "%), hsl(180, " + s + "%, " + v + "%), hsl(240, " + s + "%, " + v + "%), hsl(300, " + s + "%, " + v + "%), hsl(360, " + s + "%, " + v + "%))");
   $s.css("background", "linear-gradient(to right, hsl(" + h + ", 0%, " + v + "%), hsl(" + h + ", 100%, " + v + "%))");
   $v.css("background", "linear-gradient(to right, hsl(" + h + ", " + s + "%, 0%), hsl(" + h + ", " + s + "%, 100%))");
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
      updateHsvFromRgb();
      updatePreviews();
   });

   $("#h, #s, #v").change(function () {
      updateRgbFromHsv();
      updatePreviews();
   });

   updateHsvFromRgb();
   updatePreviews();
});
