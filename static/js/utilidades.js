function mostrarhora()
{
	var f=new Date();
	cad=agregarCero(f.getHours())+" : "+agregarCero(f.getMinutes())+" : "+agregarCero(f.getSeconds());
	return cad;
}

function agregarCero(n)
{
  if(n>9)
  {
    return n
  }
  else{
    return "0"+n;
  }
}

function validar_decimales(event) 
{
    // Allow: backspace, delete, tab, escape, and enter
    if ( event.keyCode == 46 || event.keyCode == 8 || event.keyCode == 9 || event.keyCode == 27 || event.keyCode == 13 || 
         // Allow: Ctrl+A
        (event.keyCode == 65 && event.ctrlKey === true) || 
         // Allow: home, end, left, right
        (event.keyCode >= 35 && event.keyCode <= 39)) 
    {
             // let it happen, don't do anything
    	return;
    }
    else if ((event.shiftKey || (event.keyCode < 48 || event.keyCode > 57) && (event.keyCode < 96 || event.keyCode > 105 )) &&  event.keyCode!=110 &&  event.keyCode!=190)
    {            	
        event.preventDefault(); 
    }        
}

function validar_numeros(event) 
{
    // Allow: backspace, delete, tab, escape, and enter
    if ( event.keyCode == 46 || event.keyCode == 8 || event.keyCode == 9 || event.keyCode == 27 || event.keyCode == 13 || 
         // Allow: Ctrl+A
        (event.keyCode == 65 && event.ctrlKey === true) || 
         // Allow: home, end, left, right
        (event.keyCode >= 35 && event.keyCode <= 39)) 
    {
             // let it happen, don't do anything
    	return;
    }
    else if (event.shiftKey || (event.keyCode < 48 || event.keyCode > 57) && (event.keyCode < 96 || event.keyCode > 105 ))
    {            	
        event.preventDefault(); 
    }        
}

function updateFormElementIndices(formClass) {
  var forms = $('.' + formClass);	  
  forms.each(function(i, el) {
	  $(el).find("td input, button, textarea").each(function(ind,elem) {
		  var curIndex = $(elem).attr('id').match(/\d+/);
		  $(elem).attr('id', $(elem).attr('id').replace(curIndex, i));
		  $(elem).attr('name', $(elem).attr('name').replace(curIndex, i));
      });
  });
}

function setupLoading() 
{    
	var mySpinner = null;
	var target = document.getElementById("divSpin");    
    var opts = {
        lines: 13, // The number of lines to draw
        length: 20, // The length of each line
        width: 10, // The line thickness
        radius: 30, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 8, // The rotation offset
        direction: 1, // 1: clockwise, -1: counterclockwise
        color: '#000', // #rgb or #rrggbb or array of colors
        speed: 1, // Rounds per second
        trail: 60, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'mySpin', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: '50%', // Top position relative to parent
        left: '50%' // Left position relative to parent
    };

    mySpinner = new Spinner(opts).spin(target);
    return mySpinner;
}

function removeLoading(mySpinner)
{
    mySpinner.stop();
    mySpinner = null;
}

function showLoading(mySpinner) 
{
    mySpinner.spin();
}