placeholder = {
    "blocks":
    [
        {"id":0, "type": "header", "data": {"text": "Beschreibung", "level": 2}},
        {"id":1, "type": "header", "data": {"text": "Die Veranstaltung", "level": 3}},
        {"id":2, "type": "header", "data": {"text": "Ablauf", "level": 3}},
        {"id":3, "type": "header", "data": {"text": "Übernachtung", "level": 3}},
        {"id":4, "type": "header", "data": {"text": "Wichtige Hinweise", "level": 3}},
    ], "version": "2.25.0"
}

$.getJSON({
    url: $('#editorjs').attr("data-url"),
    success: function(response) {
        if (response.empty) {
            response = placeholder
        }
        const editor = new EditorJS({
            readOnly: $('#readonly').html() != 'False',
            holder: 'editorjs',
            minHeight : 30,
            tools: {
                header: {
                    class: Header,
                    inlineToolbar: true,
                    config: {
                        placeholder: 'Header'
                    },
                 },
                list: {
                    class: List,
                    inlineToolbar: true,
                },
                marker: {
                    class:  Marker,
                },
                linkTool: LinkTool,
                table: {
                    class: Table,
                    inlineToolbar: true,
                },
                image: {
                    class: ImageTool,
                    config: {
                      endpoints: {
                        byFile: $('#guide').attr('data-url'),
                        byUrl: $('#guideurl').attr('data-url'),
                      },
                    }
                },
            },
            tunes: [],
            data: response,
        });
        // if not readonly, add save-function
        if($('#saveButton').length){
            const saveButton = document.getElementById('saveButton');
            saveButton.addEventListener('click', function () {
            editor.save()
                .then((savedData) => {
                    // collect all the saved references and send them too
                    formdata = new FormData()
                    formdata.append('data', JSON.stringify(savedData))
                    // and save the description
                    $.post({
                        processData: false,
                        contentType: false,
                        url: $('#description-save').attr("data-url"),
                        data: formdata,
                        success: function(response){
                            location.reload();
                        }
                    });
                })
            });
        }
    }
})