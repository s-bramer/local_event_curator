/*
	Directive by HTML5 UP
	html5up.net | @ajlkn
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
*/

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

let filterEventButton = document.getElementById("ftr-btn-event");

filterEventButton.addEventListener("click", () => {
  filterEventButton.classList.toggle('clicked');
  const cat_events = document.getElementsByClassName('event');
  for (i=0; i<cat_events.length;i++){
	cat_events[i].classList.toggle('hide');
	} 
})


let filterDigiEventButton = document.getElementById("ftr-btn-digi-event");

filterDigiEventButton.addEventListener("click", () => {
  filterDigiEventButton.classList.toggle('clicked');
  const cat_digi_events = document.getElementsByClassName('digital_event');
  for (i=0; i<cat_digi_events.length;i++){
	cat_digi_events[i].classList.toggle('hide');
	} 
})

let filterCourseButton = document.getElementById("ftr-btn-course");

filterCourseButton.addEventListener("click", () => {
  filterCourseButton.classList.toggle('clicked');
  const cat_courses = document.getElementsByClassName('course');
  for (i=0; i<cat_courses.length;i++){
	cat_courses[i].classList.toggle('hide');
	} 
})

let filterExhibitionButton = document.getElementById("ftr-btn-exhibition");

filterExhibitionButton.addEventListener("click", () => {
  filterExhibitionButton.classList.toggle('clicked');
  const cat_exhibitions = document.getElementsByClassName('exhibition');
  for (i=0; i<cat_exhibitions.length;i++){
	cat_exhibitions[i].classList.toggle('hide');
	} 
})