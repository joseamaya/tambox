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
	  $(el).find("td input, button").each(function(ind,elem) {
		  var curIndex = $(elem).attr('id').match(/\d+/);
		  $(elem).attr('id', $(elem).attr('id').replace(curIndex, i));
		  $(elem).attr('name', $(elem).attr('name').replace(curIndex, i));
      });
  });
}