function apercu(f,id,pb)
{
    if(document.getElementById(f).value != "")
    {
        var texte = encodeURIComponent(document.getElementById(f).value);
        var xhr;
        if (window.XMLHttpRequest) xhr = new XMLHttpRequest();
        else if (window.ActiveXObject) xhr = new ActiveXObject('Microsoft.XMLHTTP');
        else
        {
            alert('JavaScript : votre navigateur ne supporte pas les objets XMLHttpRequest...');
            return;
        }
        
        var path;
        if (!document.getElementById(pb))
            path = '/ajax-preview.html';
        else
            path = '/ajax-preview-pastebin-'+document.getElementById(pb).value+'.html';
        
        xhr.open('POST',path,true);
        
        xhr.onreadystatechange = function()
        {
            if (xhr.readyState == 4)
            {
                if (document.getElementById) {document.getElementById(id).innerHTML = xhr.responseText;}
            }
        }
        xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
        var data = 'text='+texte.replace("+","%2B");
        xhr.send(data);
    }
}
        
function tags(startTag, endTag, textareaId) {
    var field = document.getElementById(textareaId); 
    field.focus();
        
    /* === Partie 1 : on récupère la sélection === */
    if (window.ActiveXObject) {
        var textRange = document.selection.createRange();            
        var currentSelection = textRange.text;
    } else {
        var startSelection   = field.value.substring(0, field.selectionStart);
        var currentSelection = field.value.substring(field.selectionStart, field.selectionEnd);
        var endSelection     = field.value.substring(field.selectionEnd);               
    }
        
    /* === Partie 2 : on insère le tout === */
    if (window.ActiveXObject) {
        textRange.text = startTag + currentSelection + endTag;
        textRange.moveStart("character", -endTag.length - currentSelection.length);
        textRange.moveEnd("character", -endTag.length);
        textRange.select();     
    } else {
        field.value = startSelection + startTag + currentSelection + endTag + endSelection;
        field.focus();
        field.setSelectionRange(startSelection.length + startTag.length, startSelection.length + startTag.length + currentSelection.length);
    }       
}

function defaut()
{
    document.getElementById("defaut").selected = true;
}

function add_code()
{
    var value_f = document.getElementById('code_lang').options[document.getElementById('code_lang').selectedIndex].value;
    tags('    #!' + value_f + '\n    ', '', 'body');
    
    defaut();
}