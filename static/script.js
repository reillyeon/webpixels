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
      var oldPreset = $(".preset-btn.active");

      $.post("/preset/apply", { preset: preset.attr('id') })
         .always(function () {
            preset.addClass("active");
            oldPreset.removeClass("active");
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
});
