(function($) {

	var	$window = $(window),
		$body = $('body');

	// Breakpoints.
		breakpoints({
			wide:      [ '1281px',  '1680px' ],
			normal:    [ '981px',   '1280px' ],
			narrow:    [ '841px',   '980px'  ],
			narrower:  [ '737px',   '840px'  ],
			mobile:    [ '481px',   '736px'  ],
			mobilep:   [ null,      '480px'  ]
		});

	// Play initial animations on page load.
		$window.on('load', function() {
			window.setTimeout(function() {
				$body.removeClass('is-preload');
			}, 100);
		});

})(jQuery);

// Get the UP button:
let upButton = document.getElementById("up-button");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
  if (document.body.scrollTop > 1300 || document.documentElement.scrollTop > 1300) {
    upButton.style.display = "block";
  } else {
    upButton.style.display = "none";
  }
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
	document.getElementById("main").scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"})
  }

// Make the email confirmation message disappear after 5 seconds
$(document).ready(function() {
	$("#flash-message").delay(5000).fadeOut();
});