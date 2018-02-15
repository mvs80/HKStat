function getNextElement(field, fields_selector, previous) {
  var form = field.form,
      inputs = $(fields_selector, form),
      previous = previous || false;
      
  for (var e = 0; e < inputs.length; e++) {
    if (field == inputs[e]) {
      break;
    }
  }
  
  var nextElemIndex = previous ? --e : ++e;
  return inputs[(nextElemIndex + inputs.length) % inputs.length];
}

// enter2tab('input[type!=submit], select');
function enter2tab(fields_selector, get_next_element_func) {
  if (typeof(get_next_element_func) === 'undefined') {
    get_next_element_func = getNextElement;
  }

  $(fields_selector).keydown(function (event) {
    // Переопределяем поведение только для кнопок ENTER, ARROW UP/DOWN и элементов input.
    if (([13, 38, 40].indexOf(event.keyCode) == -1) || !$(this).is('input:visible')) {
      return true;
    }

    event.preventDefault();

    // ARROW UP key
    var go_back = (event.keyCode == 38);

    var nextElem = get_next_element_func(
      this, 'input:visible, textarea:visible, select:visible, button:visible', go_back
    );
    nextElem.focus();
    nextElem.select();

    return false;
  });
}

