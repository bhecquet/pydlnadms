Event.observe(window, 'load', updateScanState);

function updateScanState() {
	
	// get list of movies to scan
	var movieList = document.getElementsByClassName("titleColumn");
	for (var i=0; i < movieList.length; i++) {
		var movieEl = movieList[i];
	    var id = movieEl.getAttribute("id");
	    
	    function updateState(request) {
	    	updateState2(request, id);
	    }
	    
	    new Ajax.Request('movie/', 
	    		{method: 'get', parameters: 'movieId=' + id, onComplete: updateState, asynchronous: false})
	}
	
}

function updateState2(request, id) {
	
	var res = request.responseText;
	if (res == 'OK') {
		var movieSpan = document.getElementById(id);
		var movieStateSpan = document.getElementById('state' + id);
		
		movieSpan.innerHTML = '<a href="/pydlnadms_frontend/' + id + '/posters">' + movieSpan.innerHTML + '</a>';
		movieStateSpan.innerHTML = "OK";
	} else {
		movieStateSpan.innerHTML = "KO";
	}
	
}