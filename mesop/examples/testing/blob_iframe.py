import mesop as me


@me.page(path="/testing/blob_iframe", title="Blob iframe test")
def page():
  me.text("Testing blob iframe support")
  # This will create an iframe with a blob URL using inline JavaScript
  me.html(
    """
    <div id="blob-iframe-container">
      <script>
        // Create a blob URL and set it as iframe src
        const content = '<html><body><h1>Blob iframe content</h1></body></html>';
        const blob = new Blob([content], {type: 'text/html'});
        const blobUrl = URL.createObjectURL(blob);
        const iframe = document.createElement('iframe');
        iframe.src = blobUrl;
        iframe.id = 'test-blob-iframe';
        // Revoke the blob URL after the iframe loads to prevent memory leak
        iframe.onload = () => URL.revokeObjectURL(blobUrl);
        document.getElementById('blob-iframe-container').appendChild(iframe);
      </script>
    </div>
    """
  )
