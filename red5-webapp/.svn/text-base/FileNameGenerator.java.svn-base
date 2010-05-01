import org.apache.log4j.Logger;
import org.red5.server.api.IScope;
import org.red5.server.api.stream.IStreamFilenameGenerator;
import java.util.HashMap;
   
public class FileNameGenerator implements IStreamFilenameGenerator {
    /** Path that will store recorded videos. */
   public String recordPath = "streams/";
   /** Path that contains VOD streams. */
   public String playbackPath = "streams/";
   
   public String virtualDirectories;
   private String[] directories;
   private HashMap<String,String> vdirectories;
   private static final Logger log = Logger.getLogger("generator." + FileNameGenerator.class.getName());
   
    public void setRecordPath(String path) {
         recordPath = path;
    }
    
    public void setPlaybackPath(String path) {
         playbackPath = path;
    }
   
   // sets the virtual directories up on server startup
   
   public void setVirtualDirectories(String virtualDirectories) {
       vdirectories = new HashMap<String,String>();
       directories = virtualDirectories.split(",");
       for (int i = 0; i < directories.length; i++) {
            directories[i] = directories[i].trim();
            String[] paths = directories[i].split(";");
            
             if (!paths[0].equals("") && !paths[1].equals(""))
             {
                 vdirectories.put(paths[0], paths[1]);
             }
       }
   }
   
   public String generateFilename(IScope scope, String name,
           GenerationType type) {
       // Generate filename without an extension.
       return generateFilename(scope, name, null, type);
   }
   
   public String generateFilename(IScope scope, String name,
           String extension, GenerationType type) {
       String filename;
       
       filename = playbackPath + name;
       
       String[] paths = name.split("/");
       

       if ((vdirectories.size() > 0) && vdirectories.containsKey(paths[0]))
       {
       	filename =  vdirectories.get(paths[0]) + paths[1];
       }
       
       log.info("Generated FilePath: " + filename);
      return filename;
     }
 }
