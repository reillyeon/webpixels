function updateColor(input) {
   var value = input.val();

   console.log("Updating to " + value + ".\n");

   input.data('updating', true);
   $.post("/pixel/" + input.attr('name'), { color: value, immediate: "false" })
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
});
