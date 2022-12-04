//highlight counter for 2 seconds
function highlightFor(id,color,seconds){
    var element = document.getElementById(id)
	var close_icon = document.getElementById('filter-panel-button-close')
	// var clear_filter = document.getElementById('clear-filter')
    var origcolor = element.style.color;
    element.style.color = color;
	// clear_filter.style.color = 'white';
	close_icon.src = "static/images/tick.png";
    // element.style.fontWeight = 'bold';
    var t = setTimeout(function(){
       element.style.color = origcolor;
	//    element.style.fontWeight = 'normal'
    },(seconds*1000));
}


//buttons to make filter panel appear/disappear
let filterButton = document.getElementById("filter-button");
filterButton.addEventListener("click", () => {
	filterButton.classList.toggle('clicked');
	const filterNavBar = document.getElementsByClassName('filter-navbar');
	for (i=0; i<filterNavBar.length;i++){
		filterNavBar[i].classList.toggle('opened');
		} 
})

let filterButtonClose = document.getElementById("filter-panel-button-close");
filterButtonClose.addEventListener("click", () => {
	filterButton.classList.toggle('clicked');
	filterButtonClose.src = "static/images/close.png";
	const filterNavBar = document.getElementsByClassName('filter-navbar');
	for (i=0; i<filterNavBar.length;i++){
		filterNavBar[i].classList.toggle('opened');
		} 
})


//function to update the number of selected events//
function updateEventCount() {
	const total_events = document.getElementsByClassName('whatson');
	const hidden_event_types = document.getElementsByClassName('hide-typ')
	const hidden_event_locations = document.getElementsByClassName('hide-loc')
	const hidden_events_locations_and_types = document.getElementsByClassName('hide-loc hide-typ')
	event_count = total_events.length - (hidden_event_types.length + hidden_event_locations.length) + hidden_events_locations_and_types.length
	document.getElementById("event-count").innerHTML = "Events selected: " + event_count;
	highlightFor('event-count',"#ffa724",0.5);
}

//get filter menu items to filter event results
let filterEventType = document.getElementById("filter-event-type");
let filterEventItem = document.getElementById("filter-item-event");
let filterDigiEventItem = document.getElementById("filter-item-digi-event");
let filterCourseItem = document.getElementById("filter-item-course");
let filterExhibitionItem = document.getElementById("filter-item-exhibition");
let filterPerformanceItem = document.getElementById("filter-item-performance");
let filterLocation = document.getElementById("filter-location");
let filterVOGItem = document.getElementById("filter-location-vog");
let filterBridgendItem = document.getElementById("filter-location-bridgend");
let filterCardiffItem = document.getElementById("filter-location-cardiff");
let filterRCTItem = document.getElementById("filter-location-rct");
let filterOtherItem = document.getElementById("filter-location-other");
let clearFilter = document.getElementById("clear-filter");


/* all events selected */
filterEventType.addEventListener("click", () => {
	filterEventType.classList.toggle('clicked');
	filterEventItem.classList.remove('clicked');
	filterDigiEventItem.classList.remove('clicked');
	filterCourseItem.classList.remove('clicked');
	filterExhibitionItem.classList.remove('clicked');
	filterPerformanceItem.classList.remove('clicked');
	document.getElementById("filter-event-type").innerHTML = "Event Types (All Selected)";
  	const event_type = document.getElementsByClassName('whatson');
  	for (i=0; i<event_type.length;i++){
		event_type[i].classList.remove('hide-typ');
	} 
	updateEventCount();
})

/* select/filter events by type */
filterEventItem.addEventListener("click", () => {
	if (document.getElementById("filter-event-type").innerHTML == "Event Types (All Selected)"){
		document.getElementById("filter-event-type").innerHTML = "Event Types";
		const event_type = document.getElementsByClassName('whatson');
		for (i=0; i<event_type.length;i++){
			event_type[i].classList.toggle('hide-typ');
		} 
	}
	alert("button clicked")
	filterEventItem.classList.toggle('clicked');
	const cat_events = document.getElementsByClassName('event');
	for (i=0; i<cat_events.length;i++){
		cat_events[i].classList.toggle('hide-typ');
	} 
	updateEventCount();
})

filterDigiEventItem.addEventListener("click", () => {
	if (document.getElementById("filter-event-type").innerHTML == "Event Types (All Selected)"){
		document.getElementById("filter-event-type").innerHTML = "Event Types";
		const event_type = document.getElementsByClassName('whatson');
		for (i=0; i<event_type.length;i++){
			event_type[i].classList.toggle('hide-typ');
		} 
	}
	filterDigiEventItem.classList.toggle('clicked');
	const cat_digi_events = document.getElementsByClassName('digital_event');
	for (i=0; i<cat_digi_events.length;i++){
		cat_digi_events[i].classList.toggle('hide-typ');
	} 
	updateEventCount();
})
	
filterCourseItem.addEventListener("click", () => {
	if (document.getElementById("filter-event-type").innerHTML == "Event Types (All Selected)"){
		document.getElementById("filter-event-type").innerHTML = "Event Types";
		const event_type = document.getElementsByClassName('whatson');
		for (i=0; i<event_type.length;i++){
			event_type[i].classList.toggle('hide-typ');
		} 
	}
	filterCourseItem.classList.toggle('clicked');
	const cat_courses = document.getElementsByClassName('course');
	for (i=0; i<cat_courses.length;i++){
		cat_courses[i].classList.toggle('hide-typ');
	} 
	updateEventCount();
})
	
filterExhibitionItem.addEventListener("click", () => {
	if (document.getElementById("filter-event-type").innerHTML == "Event Types (All Selected)"){
		document.getElementById("filter-event-type").innerHTML = "Event Types";
		const event_type = document.getElementsByClassName('whatson');
		for (i=0; i<event_type.length;i++){
			event_type[i].classList.toggle('hide-typ');
		} 
	}
	filterExhibitionItem.classList.toggle('clicked');
	const cat_exhibitions = document.getElementsByClassName('exhibition');
	for (i=0; i<cat_exhibitions.length;i++){
		cat_exhibitions[i].classList.toggle('hide-typ');
	} 
	updateEventCount();
})

filterPerformanceItem.addEventListener("click", () => {
	if (document.getElementById("filter-event-type").innerHTML == "Event Types (All Selected)"){
		document.getElementById("filter-event-type").innerHTML = "Event Types";
		const event_type = document.getElementsByClassName('whatson');
		for (i=0; i<event_type.length;i++){
			event_type[i].classList.toggle('hide-typ');
		} 
	}
	filterPerformanceItem.classList.toggle('clicked');
	const cat_performance = document.getElementsByClassName('performance');
	for (i=0; i<cat_performance.length;i++){
		cat_performance[i].classList.toggle('hide-typ');
	} 
	updateEventCount();
})


/* all locations selected */
filterLocation.addEventListener("click", () => {
	filterLocation.classList.toggle('clicked');
	filterVOGItem.classList.remove('clicked');
	filterBridgendItem.classList.remove('clicked');
	filterCardiffItem.classList.remove('clicked');
	filterRCTItem.classList.remove('clicked');
	filterOtherItem.classList.remove('clicked');
	document.getElementById("filter-location").innerHTML = "Event Locations (All Selected)";
  	const event_loc = document.getElementsByClassName('whatson');
  	for (i=0; i<event_loc.length;i++){
		event_loc[i].classList.remove('hide-loc');
	} 
	updateEventCount();
})

/* select/filter events by type */
filterVOGItem.addEventListener("click", () => {
	if (document.getElementById("filter-location").innerHTML == "Event Locations (All Selected)"){
		document.getElementById("filter-location").innerHTML = "Event Locations";
		const event_loc = document.getElementsByClassName('whatson');
		for (i=0; i<event_loc.length;i++){
			event_loc[i].classList.toggle('hide-loc');
		} 
	}
	filterVOGItem.classList.toggle('clicked');
	const vog_loc = document.getElementsByClassName('vog');
	for (i=0; i<vog_loc.length;i++){
		vog_loc[i].classList.toggle('hide-loc');
	} 
	updateEventCount();
})

filterBridgendItem.addEventListener("click", () => {
	if (document.getElementById("filter-location").innerHTML == "Event Locations (All Selected)"){
		document.getElementById("filter-location").innerHTML = "Event Locations";
		const event_loc = document.getElementsByClassName('whatson');
		for (i=0; i<event_loc.length;i++){
			event_loc[i].classList.toggle('hide-loc');
		} 
	}
	filterBridgendItem.classList.toggle('clicked');
	const brd_loc = document.getElementsByClassName('brd');
	for (i=0; i<brd_loc.length;i++){
		brd_loc[i].classList.toggle('hide-loc');
	} 
	updateEventCount();
})
	
filterCardiffItem.addEventListener("click", () => {
	if (document.getElementById("filter-location").innerHTML == "Event Locations (All Selected)"){
		document.getElementById("filter-location").innerHTML = "Event Locations";
		const event_loc = document.getElementsByClassName('whatson');
		for (i=0; i<event_loc.length;i++){
			event_loc[i].classList.toggle('hide-loc');
		} 
	}
	filterCardiffItem.classList.toggle('clicked');
	const cff_loc = document.getElementsByClassName('cff');
	for (i=0; i<cff_loc.length;i++){
		cff_loc[i].classList.toggle('hide-loc');
	} 
	updateEventCount();
})
	
filterRCTItem.addEventListener("click", () => {
	if (document.getElementById("filter-location").innerHTML == "Event Locations (All Selected)"){
		document.getElementById("filter-location").innerHTML = "Event Locations";
		const event_loc = document.getElementsByClassName('whatson');
		for (i=0; i<event_loc.length;i++){
			event_loc[i].classList.toggle('hide-loc');
		} 
	}
	filterRCTItem.classList.toggle('clicked');
	const rct_loc = document.getElementsByClassName('rct');
	for (i=0; i<rct_loc.length;i++){
		rct_loc[i].classList.toggle('hide-loc');
	} 
	updateEventCount();
})


filterOtherItem.addEventListener("click", () => {
	if (document.getElementById("filter-location").innerHTML == "Event Locations (All Selected)"){
		document.getElementById("filter-location").innerHTML = "Event Locations";
		const event_loc = document.getElementsByClassName('whatson');
		for (i=0; i<event_loc.length;i++){
			event_loc[i].classList.toggle('hide-loc');
		} 
	}
	filterOtherItem.classList.toggle('clicked');
	const oth_loc = document.getElementsByClassName('oth');
	for (i=0; i<oth_loc.length;i++){
		oth_loc[i].classList.toggle('hide-loc');
	} 
	updateEventCount();
})


/* clear all filters */
clearFilter.addEventListener("click", () => {
	// clear_filter.style.color = 'blue';
	filterEventItem.classList.remove('clicked');
	filterDigiEventItem.classList.remove('clicked');
	filterCourseItem.classList.remove('clicked');
	filterExhibitionItem.classList.remove('clicked');
	filterPerformanceItem.classList.remove('clicked');
	filterVOGItem.classList.remove('clicked');
	filterBridgendItem.classList.remove('clicked');
	filterCardiffItem.classList.remove('clicked');
	filterRCTItem.classList.remove('clicked');
	filterOtherItem.classList.remove('clicked');
	document.getElementById("filter-location").innerHTML = "Event Locations (All Selected)";
	document.getElementById("filter-event-type").innerHTML = "Event Types (All Selected)";
  	const event_loc = document.getElementsByClassName('whatson');
  	for (i=0; i<event_loc.length;i++){
		event_loc[i].classList.remove('hide-typ');
		event_loc[i].classList.remove('hide-loc');
	} 
	// var clear_filter = document.getElementById('clear-filter')
	// clear_filter.style.color = '#9ca0a3';
	updateEventCount();
})