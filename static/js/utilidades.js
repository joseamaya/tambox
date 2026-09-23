function mostrarhora()
{
	var f=new Date();
	return agregarCero(f.getHours())+":"+agregarCero(f.getMinutes())+":"+agregarCero(f.getSeconds());
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
  document.querySelectorAll('.' + formClass).forEach(function (row, index) {
    row.querySelectorAll("td input, button, textarea").forEach(function (element) {
      var match = element.id && element.id.match(/\d+/);
      if (match) {
        element.id = element.id.replace(match[0], index);
      }
      if (element.name) {
        element.name = element.name.replace(/\d+/, index);
      }
    });
  });
}

