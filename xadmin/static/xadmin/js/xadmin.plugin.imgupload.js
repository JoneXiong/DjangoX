(function($) {

    function previewImage(file)
    {
	if (!file.files[0]){
		return;
	}
        // Create a new instance of the FileReader
        var reader = new FileReader();
        // Read the local file as a DataURL
        reader.readAsDataURL(file.files[0]);
        // When loaded, set image data as background of div
        reader.onloadend = function(){
            $(file).prev().attr('src', this.result);	
        }
    }

    $(function(){
        $('.img-file-ext').change(function(){
            previewImage(this);	
        });
    });

})(jQuery);
