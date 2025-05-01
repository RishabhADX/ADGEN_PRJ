def show_video_production():
    """Video Production page"""
    st.title("Video Production")
    
    # Progress indicator
    st.markdown("""
    <div class="progress-indicator">
        <div class="progress-step">
            <div class="step-circle completed">1</div>
            <div>Content</div>
        </div>
        <div class="progress-step">
            <div class="step-circle completed">2</div>
            <div>Visual</div>
        </div>
        <div class="progress-step">
            <div class="step-circle completed">3</div>
            <div>Audio</div>
        </div>
        <div class="progress-step">
            <div class="step-circle active">4</div>
            <div>Video</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">5</div>
            <div>Export</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    current_project = st.session_state.current_project
    
    # Check if previous steps have been completed
    if (current_project not in st.session_state.scripts or 
        current_project not in st.session_state.images or 
        current_project not in st.session_state.audio):
        st.warning("Please complete the previous steps before proceeding to Video Production.")
        
        missing_steps = []
        if current_project not in st.session_state.scripts:
            missing_steps.append("Content Generation")
        if current_project not in st.session_state.images:
            missing_steps.append("Visual Asset Creation")
        if current_project not in st.session_state.audio:
            missing_steps.append("Voice & Audio")
        
        st.info(f"Missing steps: {', '.join(missing_steps)}")
        
        if st.button("Go Back"):
            # Determine which step to go back to
            if current_project not in st.session_state.scripts:
                st.session_state.current_step = 1
            elif current_project not in st.session_state.images:
                st.session_state.current_step = 2
            elif current_project not in st.session_state.audio:
                st.session_state.current_step = 3
            
            st.experimental_rerun()
        return
    
    # Initialize videos in session if not existing
    if current_project not in st.session_state.videos:
        st.session_state.videos[current_project] = {
            "avatar": None,
            "aspect_ratio": "16:9",
            "target_platforms": [],
            "caption_style": "standard",
            "transitions": "fade",
            "completed_video": None,
            "video_settings": {
                "intro_screen": True,
                "outro_screen": True,
                "show_captions": True,
                "logo_overlay": False,
                "logo_position": "bottom-right"
            }
        }
    
    # Video production tabs
    tabs = st.tabs(["Avatar & Style", "Video Settings", "Timeline Preview", "Generate Video"])
    
    with tabs[0]:
        st.subheader("Avatar & Style Configuration")
        
        # Avatar selection
        st.markdown("### Select Presenter Avatar")
        
        # Get avatar catalog
        avatars = get_avatar_catalog()
        
        # Display avatars in a grid
        cols = st.columns(4)
        
        for i, avatar in enumerate(avatars):
            with cols[i % 4]:
                st.image(
                    avatar["thumbnail"],
                    caption=avatar["name"],
                    use_column_width=True
                )
                
                if st.button("Select", key=f"select_avatar_{i}"):
                    st.session_state.videos[current_project]["avatar"] = avatar
                    st.success(f"Selected avatar: {avatar['name']}")
        
        # Display selected avatar
        if st.session_state.videos[current_project]["avatar"]:
            avatar = st.session_state.videos[current_project]["avatar"]
            
            st.markdown("### Selected Avatar")
            st.image(
                avatar["preview"],
                caption=f"{avatar['name']} - {avatar['style']}",
                width=300
            )
            
            st.markdown(f"""
            **Description:** {avatar['description']}
            
            **Best for:** {avatar['best_for']}
            """)
            
            # Remove button
            if st.button("Remove Avatar"):
                st.session_state.videos[current_project]["avatar"] = None
                st.success("Avatar removed")
        
        # Video style options
        st.markdown("### Video Style Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Aspect ratio
            aspect_ratio = st.selectbox(
                "Aspect Ratio",
                ["16:9 (Landscape)", "1:1 (Square)", "9:16 (Portrait/Mobile)"],
                index=0 if st.session_state.videos[current_project]["aspect_ratio"] == "16:9" else
                       1 if st.session_state.videos[current_project]["aspect_ratio"] == "1:1" else 2
            )
            
            # Target platforms
            target_platforms = st.multiselect(
                "Target Platforms",
                ["YouTube", "Facebook", "Instagram", "Twitter", "LinkedIn", "TikTok", "Website"],
                default=st.session_state.videos[current_project]["target_platforms"]
            )
        
        with col2:
            # Caption style
            caption_style = st.selectbox(
                "Caption Style",
                ["Standard", "Creative", "Minimal", "Bold", "Elegant"],
                index=["Standard", "Creative", "Minimal", "Bold", "Elegant"].index(
                    st.session_state.videos[current_project]["caption_style"].title()
                ) if st.session_state.videos[current_project]["caption_style"] in 
                ["standard", "creative", "minimal", "bold", "elegant"] else 0
            )
            
            # Transitions
            transitions = st.selectbox(
                "Scene Transitions",
                ["Fade", "Cut", "Dissolve", "Slide", "Zoom"],
                index=["Fade", "Cut", "Dissolve", "Slide", "Zoom"].index(
                    st.session_state.videos[current_project]["transitions"].title()
                ) if st.session_state.videos[current_project]["transitions"] in 
                ["fade", "cut", "dissolve", "slide", "zoom"] else 0
            )
        
        # Save style settings
        if st.button("Save Style Settings", type="primary"):
            # Extract aspect ratio value
            aspect_ratio_value = "16:9"
            if "(Square)" in aspect_ratio:
                aspect_ratio_value = "1:1"
            elif "(Portrait" in aspect_ratio:
                aspect_ratio_value = "9:16"
            
            # Update session state
            st.session_state.videos[current_project]["aspect_ratio"] = aspect_ratio_value
            st.session_state.videos[current_project]["target_platforms"] = target_platforms
            st.session_state.videos[current_project]["caption_style"] = caption_style.lower()
            st.session_state.videos[current_project]["transitions"] = transitions.lower()
            
            st.success("Video style settings saved!")
    
    with tabs[1]:
        st.subheader("Video Settings")
        
        # Video settings form
        video_settings = st.session_state.videos[current_project]["video_settings"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Intro and outro screens
            intro_screen = st.checkbox(
                "Include Intro Screen",
                value=video_settings["intro_screen"]
            )
            
            outro_screen = st.checkbox(
                "Include Outro Screen",
                value=video_settings["outro_screen"]
            )
        
        with col2:
            # Caption and logo settings
            show_captions = st.checkbox(
                "Show Captions",
                value=video_settings["show_captions"]
            )
            
            logo_overlay = st.checkbox(
                "Add Logo Overlay",
                value=video_settings["logo_overlay"]
            )
        
        # Logo settings (only shown if logo overlay is enabled)
        if logo_overlay:
            st.subheader("Logo Settings")
            
            logo_position = st.selectbox(
                "Logo Position",
                ["Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"],
                index=["Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"].index(
                    video_settings["logo_position"].title().replace("-", "-")
                ) if video_settings["logo_position"] in 
                ["top-left", "top-right", "bottom-left", "bottom-right"] else 3
            )
            
            # Logo upload
            uploaded_logo = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"])
            
            if uploaded_logo is not None:
                # Process uploaded logo
                image = Image.open(uploaded_logo)
                
                # Display logo preview
                st.image(image, caption="Logo Preview", width=200)
                
                st.success(f"Logo uploaded: {uploaded_logo.name}")
        
        # Save video settings
        if st.button("Save Video Settings", type="primary"):
            # Update session state
            st.session_state.videos[current_project]["video_settings"] = {
                "intro_screen": intro_screen,
                "outro_screen": outro_screen,
                "show_captions": show_captions,
                "logo_overlay": logo_overlay,
                "logo_position": logo_position.lower().replace(" ", "-") if logo_overlay else "bottom-right"
            }
            
            st.success("Video settings saved!")
    
    with tabs[2]:
        st.subheader("Timeline Preview")
        
        # Get scenes from script
        scenes = st.session_state.scripts[current_project]["scenes"]
        
        # Timeline preview
        st.markdown("### Video Timeline")
        
        # Calculate total duration
        total_duration = 0
        scene_durations = []
        
        for i, scene in enumerate(scenes):
            scene_id = f"scene_{i+1}"
            
            # Get audio clips for this scene
            audio_duration = 0
            
            # Check for dialogue audio
            for j, (audio_id, audio_data) in enumerate(st.session_state.audio[current_project]["generated_audio"].items()):
                if audio_id.startswith(scene_id):
                    audio_duration += audio_data["duration"]
            
            # If no audio, use a default duration
            if audio_duration == 0:
                audio_duration = 5.0
            
            # Add transition time
            scene_duration = audio_duration + 0.5  # Add 0.5 seconds for transition
            scene_durations.append(scene_duration)
            total_duration += scene_duration
        
        # Add intro and outro times if enabled
        if st.session_state.videos[current_project]["video_settings"]["intro_screen"]:
            total_duration += 3.0  # 3 seconds for intro
        
        if st.session_state.videos[current_project]["video_settings"]["outro_screen"]:
            total_duration += 5.0  # 5 seconds for outro
        
        # Display total duration
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        st.markdown(f"**Estimated Total Duration:** {minutes}:{seconds:02d}")
        
        # Timeline visualization
        st.markdown("### Timeline Visualization")
        
        # Create a timeline chart
        timeline_data = []
        current_time = 0
        
        # Add intro if enabled
        if st.session_state.videos[current_project]["video_settings"]["intro_screen"]:
            timeline_data.append({
                "name": "Intro",
                "start": 0,
                "end": 3,
                "type": "intro"
            })
            current_time = 3
        
        # Add scenes
        for i, (scene, duration) in enumerate(zip(scenes, scene_durations)):
            timeline_data.append({
                "name": f"Scene {i+1}",
                "start": current_time,
                "end": current_time + duration,
                "type": "scene"
            })
            current_time += duration
        
        # Add outro if enabled
        if st.session_state.videos[current_project]["video_settings"]["outro_screen"]:
            timeline_data.append({
                "name": "Outro",
                "start": current_time,
                "end": current_time + 5,
                "type": "outro"
            })
        
        # Create a simple timeline visualization
        max_time = total_duration
        timeline_height = 50
        
        st.markdown("<div style='background-color: #f0f0f0; height: 50px; position: relative;'>", unsafe_allow_html=True)
        
        for item in timeline_data:
            start_percent = (item["start"] / max_time) * 100
            width_percent = ((item["end"] - item["start"]) / max_time) * 100
            
            color = "#4da6ff"  # Default color
            if item["type"] == "intro":
                color = "#32CD32"  # Green
            elif item["type"] == "outro":
                color = "#FF8C00"  # Orange
            
            st.markdown(
                f"""
                <div style='
                    position: absolute;
                    left: {start_percent}%;
                    width: {width_percent}%;
                    height: 100%;
                    background-color: {color};
                    text-align: center;
                    color: white;
                    line-height: 50px;
                    overflow: hidden;
                    white-space: nowrap;
                    border-right: 1px solid white;
                '>
                    {item["name"]}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Timeline key
        st.markdown("""
        **Color Key:**
        <span style="display: inline-block; width: 20px; height: 20px; background-color: #32CD32; margin-right: 5px;"></span> Intro
        <span style="display: inline-block; width: 20px; height: 20px; background-color: #4da6ff; margin-right: 5px; margin-left: 15px;"></span> Scenes
        <span style="display: inline-block; width: 20px; height: 20px; background-color: #FF8C00; margin-right: 5px; margin-left: 15px;"></span> Outro
        """, unsafe_allow_html=True)
        
        # Scene preview section
        st.markdown("### Scene Previews")
        
        # Create tabs for scene previews
        scene_tabs = st.tabs([f"Scene {i+1}" for i in range(len(scenes))])
        
        for i, (scene_tab, scene) in enumerate(zip(scene_tabs, scenes)):
            with scene_tab:
                scene_id = f"scene_{i+1}"
                
                # Scene layout with columns
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Scene content
                    st.markdown(f"**{scene['heading']}**")
                    st.markdown(f"*{scene['content']}*")
                    
                    # Display dialogue
                    if "dialogue" in scene and scene["dialogue"]:
                        st.markdown("**Dialogue:**")
                        for line in scene["dialogue"]:
                            st.markdown(f"- **{line['character']}:** {line['text']}")
                    
                    # Audio information
                    st.markdown("**Audio Clips:**")
                    
                    audio_found = False
                    for audio_id, audio_data in st.session_state.audio[current_project]["generated_audio"].items():
                        if audio_id.startswith(scene_id):
                            st.markdown(f"- {audio_data['character']}: *\"{audio_data['text']}\"* ({audio_data['duration']:.1f}s)")
                            audio_found = True
                    
                    if not audio_found:
                        st.markdown("*No audio clips found for this scene*")
                
                with col2:
                    # Display image
                    if scene_id in st.session_state.images[current_project]["generated_images"]:
                        image_data = st.session_state.images[current_project]["generated_images"][scene_id]
                        st.image(image_data["url"], caption="Scene Image", use_column_width=True)
                    elif scene_id in st.session_state.images[current_project]["custom_images"]:
                        image_data = st.session_state.images[current_project]["custom_images"][scene_id]
                        st.image(image_data["url"], caption="Custom Image", use_column_width=True)
                    else:
                        st.info("No image available for this scene")
    
    with tabs[3]:
        st.subheader("Generate Video")
        
        # Check if all required components are available
        missing_components = []
        
        if not st.session_state.projects[current_project]["progress"]["content_generation"]:
            missing_components.append("Script/content")
        if not st.session_state.projects[current_project]["progress"]["visual_assets"]:
            missing_components.append("Visual assets")
        if not st.session_state.projects[current_project]["progress"]["audio"]:
            missing_components.append("Audio")
        
        if missing_components:
            st.warning(f"Missing components: {', '.join(missing_components)}")
            st.info("Please complete all required components before generating the video.")
        else:
            # Video generation options
            st.markdown("### Video Generation Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                video_quality = st.select_slider(
                    "Video Quality",
                    options=["Standard (720p)", "High (1080p)", "Premium (4K)"],
                    value="High (1080p)"
                )
                
                processing_priority = st.select_slider(
                    "Processing Priority",
                    options=["Normal", "High (Faster)"],
                    value="Normal"
                )
            
            with col2:
                render_mode = st.radio(
                    "Render Mode",
                    ["Draft (Fast)", "Standard", "High Quality (Slower)"],
                    index=1
                )
            
            # Generate video button
            if st.button("Generate Video", type="primary"):
                with st.spinner("Generating video..."):
                    # Simulate video generation process
                    progress_bar = st.progress(0)
                    
                    # Different steps in the video generation process
                    steps = [
                        "Initializing project",
                        "Preparing assets",
                        "Processing scene transitions",
                        "Synchronizing audio",
                        "Rendering video",
                        "Applying effects",
                        "Finalizing"
                    ]
                    
                    for i, step in enumerate(steps):
                        # Update progress text and bar
                        progress_text = st.empty()
                        progress_text.markdown(f"**{step}...**")
                        
                        # Calculate progress percentage
                        progress = i / len(steps)
                        progress_bar.progress(progress)
                        
                        # Simulate processing time
                        time.sleep(1)
                    
                    # Complete the progress
                    progress_bar.progress(1.0)
                    progress_text.markdown("**Video generated successfully!**")
                    
                    # Generate a mock video URL
                    timestamp = int(time.time())
                    video_url = f"https://example.com/videos/project_{current_project}_{timestamp}.mp4"
                    
                    # Save video information
                    st.session_state.videos[current_project]["completed_video"] = {
                        "url": video_url,
                        "quality": video_quality,
                        "render_mode": render_mode,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "duration": total_duration
                    }
                    
                    # Mark video production as complete
                    st.session_state.projects[current_project]["progress"]["video_production"] = True
                    
                    time.sleep(1)
                
                # Show success message
                st.success("Video has been generated successfully!")
                
                # Display video preview
                st.markdown("### Video Preview")
                
                # In a real implementation, this would be a video player
                # For now, just display a placeholder image
                st.image(
                    f"https://via.placeholder.com/800x450?text=Generated+Video+Preview+{timestamp}",
                    caption="Video Preview",
                    use_column_width=True
                )
                
                # Continue button
                if st.button("Continue to Export & Share", type="primary"):
                    st.session_state.current_step = 5
                    st.experimental_rerun()
            
            # Information about generation times
            st.info("""
            **Estimated generation times:**
            - Draft: ~1-2 minutes
            - Standard: ~3-5 minutes
            - High Quality: ~8-10 minutes
            
            Actual times may vary based on project complexity and system load.
            """)

#################################################
# EXPORT & SHARE MODULE
#################################################

def format_duration(seconds):
    """Format duration in seconds to MM:SS format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    
    return f"{minutes}:{remaining_seconds:02d}"

def show_export_share():
    """Export & Share page"""
    st.title("Export & Share")
    
    # Progress indicator
    st.markdown("""
    <div class="progress-indicator">
        <div class="progress-step">
            <div class="step-circle completed">1</div>
            <div>Content</div>
        </div>
        <div class="progress-step">
            <div class="step-circle completed">2</div>
            <div>Visual</div>
        </div>
        <div class="progress-step">
            <div class="step-circle completed">3</div>
            <div>Audio</div>
        </div>
        <div class="progress-step">
            <div class="step-circle completed">4</div>
            <div>Video</div>
        </div>
        <div class="progress-step">
            <div class="step-circle active">5</div>
            <div>Export</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    current_project = st.session_state.current_project
    
    # Check if video has been generated
    if (current_project not in st.session_state.videos or 
        "completed_video" not in st.session_state.videos[current_project] or 
        st.session_state.videos[current_project]["completed_video"] is None):
        st.warning("Please generate a video first in the Video Production section.")
        if st.button("Go to Video Production"):
            st.session_state.current_step = 4
            st.experimental_rerun()
        return
    
    # Get video data
    video_data = st.session_state.videos[current_project]["completed_video"]
    
    # Export & share tabs
    tabs = st.tabs(["Video Preview", "Download Options", "Share", "Project Report"])
    
    with tabs[0]:
        st.subheader("Video Preview")
        
        # Display video information
        st.markdown(f"""
        ### {st.session_state.projects[current_project]['name']}
        
        **Generated on:** {video_data['created_at']}
        
        **Duration:** {format_duration(video_data['duration'])}
        
        **Quality:** {video_data['quality']}
        """)
        
        # Video player
        st.markdown("### Video Player")
        
        # In a real implementation, this would be an embedded video player
        # For now, just display a placeholder image
        timestamp = video_data['url'].split('_')[-1].split('.')[0]
        st.image(
            f"https://via.placeholder.com/800x450?text=Video+Player+{timestamp}",
            caption="Video Preview",
            use_column_width=True
        )
        
        # Mock video player controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        
        with col1:
            st.button("⏮️")
        with col2:
            st.button("⏯️")
        with col3:
            st.button("⏹️")
        with col4:
            st.button("⏭️")
        with col5:
            st.button("🔊")
    
    with tabs[1]:
        st.subheader("Download Options")
        
        # File format selection
        file_format = st.selectbox(
            "File Format",
            ["MP4 (H.264)", "MP4 (H.265)", "WebM", "MOV", "AVI"],
            index=0
        )
        
        # Quality options
        quality_options = st.radio(
            "Quality",
            ["Standard (720p)", "High (1080p)", "Premium (4K)"],
            index=1 if "1080p" in video_data['quality'] else 
                   2 if "4K" in video_data['quality'] else 0
        )
        
        # Additional download options
        col1, col2 = st.columns(2)
        
        with col1:
            include_subtitles = st.checkbox("Include Subtitles", value=True)
            include_chapters = st.checkbox("Include Chapter Markers", value=True)
        
        with col2:
            optimize_for = st.selectbox(
                "Optimize For",
                ["General Purpose", "Web", "Social Media", "Mobile Devices"],
                index=0
            )
            
            max_size = st.slider(
                "Maximum File Size (MB)",
                min_value=10,
                max_value=2000,
                value=500,
                step=10
            )
        
        # Download button
        if st.button("Download Video", type="primary"):
            with st.spinner("Preparing download..."):
                # Simulate download preparation
                time.sleep(2)
                
                # Show success message with mock download link
                st.success("Video ready for download!")
                st.markdown(f"[Download {file_format.split(' ')[0]} Video ({quality_options.split(' ')[0]})]({video_data['url']})")
        
        # Additional exports
        st.subheader("Additional Exports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Audio Only (MP3)"):
                with st.spinner("Exporting audio..."):
                    time.sleep(1)
                    st.success("Audio exported!")
                    st.markdown(f"[Download Audio (MP3)]({video_data['url'].replace('.mp4', '.mp3')})")
        
        with col2:
            if st.button("Export Subtitles (SRT)"):
                with st.spinner("Exporting subtitles..."):
                    time.sleep(1)
                    st.success("Subtitles exported!")
                    st.markdown(f"[Download Subtitles (SRT)]({video_data['url'].replace('.mp4', '.srt')})")
        
        with col3:
            if st.button("Export Thumbnail (JPG)"):
                with st.spinner("Exporting thumbnail..."):
                    time.sleep(1)
                    st.success("Thumbnail exported!")
                    st.markdown(f"[Download Thumbnail (JPG)]({video_data['url'].replace('.mp4', '.jpg')})")
    
    with tabs[2]:
        st.subheader("Share")
        
        # Project visibility settings
        visibility = st.radio(
            "Project Visibility",
            ["Private (Only accessible with link)", "Public (Anyone can view)"],
            index=0
        )
        
        # Share settings
        st.markdown("### Share Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            allow_comments = st.checkbox("Allow Comments", value=True)
            allow_downloads = st.checkbox("Allow Downloads", value=True)
        
        with col2:
            expiration = st.selectbox(
                "Link Expiration",
                ["Never", "24 Hours", "7 Days", "30 Days"],
                index=0
            )
            
            password_protect = st.checkbox("Password Protect", value=False)
        
        # Password field (only shown if password protect is enabled)
        if password_protect:
            password = st.text_input("Set Password", type="password")
        
        # Generate share link
        if st.button("Generate Share Link", type="primary"):
            with st.spinner("Generating share link..."):
                time.sleep(1)
                
                # Generate a mock share link
                project_id = st.session_state.current_project.lower().replace(" ", "-")
                timestamp = int(time.time())
                share_link = f"https://example.com/share/{project_id}-{timestamp}"
                
                # Show success message with mock share link
                st.success("Share link generated!")
                st.code(share_link)
                
                # Copy button
                if st.button("Copy Link"):
                    st.info("Link copied to clipboard!")
        
        # Social media sharing
        st.markdown("### Share on Social Media")
        
        social_cols = st.columns(4)
        
        with social_cols[0]:
            if st.button("Share on Facebook"):
                st.info("Opening Facebook share dialog...")
        
        with social_cols[1]:
            if st.button("Share on Twitter"):
                st.info("Opening Twitter share dialog...")
        
        with social_cols[2]:
            if st.button("Share on LinkedIn"):
                st.info("Opening LinkedIn share dialog...")
        
        with social_cols[3]:
            if st.button("Share on YouTube"):
                st.info("Opening YouTube upload dialog...")
        
        # Email sharing
        st.markdown("### Share via Email")
        
        email_recipient = st.text_input("Recipient Email")
        email_subject = st.text_input("Subject", value=f"Check out my video: {st.session_state.projects[current_project]['name']}")
        email_message = st.text_area("Message", value="I created this video using the AI Creative Suite and wanted to share it with you.")
        
        if st.button("Send Email"):
            if email_recipient:
                with st.spinner("Sending email..."):
                    time.sleep(1)
                    st.success(f"Email sent to {email_recipient}!")
            else:
                st.error("Please enter a recipient email address.")
    
    with tabs[3]:
        st.subheader("Project Report")
        
        # Generate project report
        st.markdown("### Project Summary")
        
        project_data = st.session_state.projects[current_project]
        
        # Project information
        st.markdown(f"""
        **Project Name:** {project_data['name']}
        
        **Description:** {project_data['description']}
        
        **Created On:** {project_data['created_at']}
        
        **Project Type:** {project_data['type']}
        
        **Target Platforms:** {', '.join(project_data['target_platforms'])}
        
        **Aspect Ratio:** {project_data['aspect_ratio']}
        """)
        
        # Asset usage
        st.markdown("### Asset Usage")
        
        # Count asset types
        scenes_count = len(st.session_state.scripts[current_project]['scenes'])
        images_count = len(st.session_state.images[current_project]['generated_images']) + len(st.session_state.images[current_project]['custom_images'])
        audio_count = len(st.session_state.audio[current_project]['generated_audio'])
        
        # Create asset counters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Scenes", scenes_count)
        
        with col2:
            st.metric("Images", images_count)
        
        with col3:
            st.metric("Audio Clips", audio_count)
        
        with col4:
            minutes = int(video_data['duration'] // 60)
            seconds = int(video_data['duration'] % 60)
            st.metric("Video Duration", f"{minutes}:{seconds:02d}")
        
        # Export project report
        if st.button("Export Project Report (PDF)"):
            with st.spinner("Generating PDF report..."):
                time.sleep(2)
                st.success("PDF report generated!")
                st.markdown(f"[Download Project Report (PDF)](https://example.com/reports/{current_project.lower().replace(' ', '-')}.pdf)")
        
        # Start new project button
        if st.button("Start New Project", type="primary"):
            # Reset session state to create a new project
            st.session_state.show_project_creation = True
            st.session_state.current_project = None
            st.session_state.current_step = 1
            st.experimental_rerun()

#################################################
# MAIN APPLICATION
#################################################

def main():
    """Main application function"""
    # Load custom CSS
    load_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar
    create_sidebar()
    
    # Show project creation dialog if requested
    if 'show_project_creation' in st.session_state and st.session_state.show_project_creation:
        show_project_creation()
    
    # If no project is selected, show welcome screen
    if not st.session_state.current_project:
        st.title("Welcome to AI Creative Suite")
        st.markdown("""
        ## Create Professional Videos with AI
        
        This suite provides a comprehensive end-to-end solution for creating videos from scripts, 
        screenplays, or marketing briefs using artificial intelligence.
        
        ### Features:
        - Script generation and editing with AI assistance
        - Scene-by-scene image generation
        - Voice and audio creation with a catalog of AI voices
        - Professional video production with customizable templates
        - Complete workflow management
        
        Get started by creating a new project from the sidebar.
        """)
        
        # Sample showcase
        st.subheader("Sample Showcase")
        cols = st.columns(3)
        with cols[0]:
            st.image("https://via.placeholder.com/300x200?text=Sample+Video+1", use_column_width=True)
            st.markdown("**Marketing Video Example**")
        with cols[1]:
            st.image("https://via.placeholder.com/300x200?text=Sample+Video+2", use_column_width=True)
            st.markdown("**Product Demo Example**")
        with cols[2]:
            st.image("https://via.placeholder.com/300x200?text=Sample+Video+3", use_column_width=True)
            st.markdown("**Social Media Ad Example**")
    else:
        # Show the appropriate step based on session state
        if st.session_state.current_step == 1:
            show_content_generation()
        elif st.session_state.current_step == 2:
            show_visual_asset_creation()
        elif st.session_state.current_step == 3:
            show_voice_audio()
        elif st.session_state.current_step == 4:
            show_video_production()
        elif st.session_state.current_step == 5:
            show_export_share()

if __name__ == "__main__":
    main()#################################################
# VOICE & AUDIO MODULE
#################################################

def get_voice_catalog(gender_filter, style_filter, language_filter):
    """Get voice catalog filtered by criteria
    
    Args:
        gender_filter: List of gender filters
        style_filter: List of style filters
        language_filter: List of language filters
        
    Returns:
        list: Filtered list of voice dictionaries
    """
    # Mock voice catalog
    all_voices = [
        {
            "id": "voice_1",
            "name": "Michael",
            "gender": "Male",
            "style": "Professional",
            "language": "English (US)"
        },
        {
            "id": "voice_2",
            "name": "Sarah",
            "gender": "Female",
            "style": "Professional",
            "language": "English (US)"
        },
        {
            "id": "voice_3",
            "name": "James",
            "gender": "Male",
            "style": "Casual",
            "language": "English (UK)"
        },
        {
            "id": "voice_4",
            "name": "Emily",
            "gender": "Female",
            "style": "Enthusiastic",
            "language": "English (US)"
        },
        {
            "id": "voice_5",
            "name": "David",
            "gender": "Male",
            "style": "Serious",
            "language": "English (UK)"
        },
        {
            "id": "voice_6",
            "name": "Maria",
            "gender": "Female",
            "style": "Professional",
            "language": "Spanish"
        },
        {
            "id": "voice_7",
            "name": "Jean",
            "gender": "Male",
            "style": "Casual",
            "language": "French"
        },
        {
            "id": "voice_8",
            "name": "Alex",
            "gender": "Neutral",
            "style": "Professional",
            "language": "English (US)"
        },
        {
            "id": "voice_9",
            "name": "Yuki",
            "gender": "Female",
            "style": "Friendly",
            "language": "Japanese"
        },
        {
            "id": "voice_10",
            "name": "Li Wei",
            "gender": "Male",
            "style": "Professional",
            "language": "Chinese"
        },
        {
            "id": "voice_11",
            "name": "Hannah",
            "gender": "Female",
            "style": "Serious",
            "language": "German"
        },
        {
            "id": "voice_12",
            "name": "Taylor",
            "gender": "Neutral",
            "style": "Enthusiastic",
            "language": "English (US)"
        }
    ]
    
    # Apply filters
    filtered_voices = []
    for voice in all_voices:
        if voice["gender"] in gender_filter and voice["style"] in style_filter and voice["language"] in language_filter:
            filtered_voices.append(voice)
    
    return filtered_voices

def get_all_characters(scenes):
    """Extract all characters from script scenes
    
    Args:
        scenes: List of scene dictionaries
        
    Returns:
        list: List of unique character names
    """
    characters = []
    
    for scene in scenes:
        if "dialogue" in scene:
            for line in scene["dialogue"]:
                character = line["character"]
                if character not in characters:
                    characters.append(character)
    
    return characters

def generate_mock_audio(text, voice_id, is_regeneration=False):
    """Generate a mock audio URL
    
    Args:
        text: Text to convert to speech
        voice_id: ID of the selected voice
        is_regeneration: Whether this is a regeneration
        
    Returns:
        str: URL to the mock audio file
    """
    # In a real implementation, this would call a text-to-speech API
    # For now, just return a mock URL
    timestamp = int(time.time())
    random_id = random.randint(1, 1000)
    seed = random_id + (500 if is_regeneration else 0)  # Different seed for regeneration
    
    return f"https://example.com/audio/{voice_id}_{timestamp}_{seed}.mp3"

def get_mock_audio_duration(text):
    """Calculate approximate duration of audio based on text length
    
    Args:
        text: Text content
        
    Returns:
        float: Estimated duration in seconds
    """
    # Rough estimate: average speaking rate is about 150 words per minute
    # So about 2.5 words per second
    words = len(text.split())
    duration = words / 2.5
    
    # Add a bit of randomness for realistic variation
    duration *= random.uniform(0.9, 1.1)
    
    # Ensure minimum duration
    return max(1.0, duration)

def get_background_music(category):
    """Get background music options based on category
    
    Args:
        category: Music category
        
    Returns:
        list: List of music options
    """
    # Mock background music catalog
    music_catalog = {
        "Upbeat": [
            {
                "id": "upbeat_1",
                "title": "Positive Energy",
                "duration": "2:45",
                "description": "Bright and energetic track with a catchy melody."
            },
            {
                "id": "upbeat_2",
                "title": "Morning Sunshine",
                "duration": "3:12",
                "description": "Cheerful tune with acoustic guitars and light percussion."
            },
            {
                "id": "upbeat_3",
                "title": "Success Story",
                "duration": "2:30",
                "description": "Motivational track with a building arrangement."
            }
        ],
        "Corporate": [
            {
                "id": "corporate_1",
                "title": "Professional Growth",
                "duration": "2:20",
                "description": "Clean, modern corporate track with subtle piano."
            },
            {
                "id": "corporate_2",
                "title": "Business Solutions",
                "duration": "3:05",
                "description": "Confident and polished track for professional presentations."
            },
            {
                "id": "corporate_3",
                "title": "Innovation",
                "duration": "2:15",
                "description": "Technology-focused background music with a modern feel."
            }
        ],
        "Inspirational": [
            {
                "id": "inspire_1",
                "title": "New Horizons",
                "duration": "3:30",
                "description": "Emotional piano melody with orchestral elements."
            },
            {
                "id": "inspire_2",
                "title": "Journey of Hope",
                "duration": "4:15",
                "description": "Uplifting soundtrack with soaring strings."
            },
            {
                "id": "inspire_3",
                "title": "Overcome",
                "duration": "2:50",
                "description": "Motivational track with a powerful emotional arc."
            }
        ],
        "Cinematic": [
            {
                "id": "cinematic_1",
                "title": "Epic Revelation",
                "duration": "3:45",
                "description": "Dramatic orchestral piece with a cinematic quality."
            },
            {
                "id": "cinematic_2",
                "title": "The Discovery",
                "duration": "3:20",
                "description": "Adventure-themed soundtrack with exciting elements."
            },
            {
                "id": "cinematic_3",
                "title": "Moment of Truth",
                "duration": "4:00",
                "description": "Suspenseful track with a triumphant conclusion."
            }
        ],
        "Relaxing": [
            {
                "id": "relax_1",
                "title": "Gentle Waves",
                "duration": "3:15",
                "description": "Calming ambient music with natural elements."
            },
            {
                "id": "relax_2",
                "title": "Peaceful Mind",
                "duration": "4:30",
                "description": "Soft piano melody with subtle atmospheric textures."
            },
            {
                "id": "relax_3",
                "title": "Tranquility",
                "duration": "3:50",
                "description": "Serene background music for relaxation and focus."
            }
        ],
        "Technology": [
            {
                "id": "tech_1",
                "title": "Digital Future",
                "duration": "2:40",
                "description": "Electronic track with a modern, tech-focused sound."
            },
            {
                "id": "tech_2",
                "title": "Innovation Loop",
                "duration": "3:10",
                "description": "Cutting-edge electronic music with a technological feel."
            },
            {
                "id": "tech_3",
                "title": "Code Stream",
                "duration": "2:25",
                "description": "Minimal electronic track with a precise, digital quality."
            }
        ]
    }
    
    return music_catalog.get(category, [])

def show_voice_audio():
    """Voice & Audio page"""
    st.title("Voice & Audio System")
    
    # Progress indicator
    st.markdown("""
    <div class="progress-indicator">
        <div class="progress-step">
            <div class="step-circle">5</div>
            <div>Export</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    current_project = st.session_state.current_project
    
    # Check if script exists
    if current_project not in st.session_state.scripts or not st.session_state.scripts[current_project]["scenes"]:
        st.warning("Please create a script first in the Content Generation section.")
        if st.button("Go to Content Generation"):
            st.session_state.current_step = 1
            st.experimental_rerun()
        return
    
    # Initialize audio in session if not existing
    if current_project not in st.session_state.audio:
        st.session_state.audio[current_project] = {
            "selected_voices": {},
            "generated_audio": {},
            "background_music": None,
            "audio_settings": {
                "volume": 1.0,
                "speed": 1.0,
                "add_background_music": False,
                "background_music_volume": 0.2
            }
        }
    
    # Audio tabs
    tabs = st.tabs(["Voice Selection", "Audio Generation", "Audio Settings"])
    
    with tabs[0]:
        st.subheader("Voice Catalog")
        
        # Voice filtering
        col1, col2, col3 = st.columns(3)
        
        with col1:
            gender_filter = st.multiselect(
                "Gender",
                ["Male", "Female", "Neutral"],
                default=["Male", "Female", "Neutral"]
            )
        
        with col2:
            style_filter = st.multiselect(
                "Style",
                ["Professional", "Casual", "Enthusiastic", "Serious", "Friendly"],
                default=["Professional", "Casual"]
            )
        
        with col3:
            language_filter = st.multiselect(
                "Language",
                ["English (US)", "English (UK)", "Spanish", "French", "German", "Chinese", "Japanese"],
                default=["English (US)"]
            )
        
        # Get voice catalog
        voices = get_voice_catalog(gender_filter, style_filter, language_filter)
        
        # Display voice cards in a grid
        if voices:
            st.markdown("### Available Voices")
            
            # Display voices in a 3-column grid
            for i in range(0, len(voices), 3):
                cols = st.columns(3)
                
                for j in range(3):
                    if i + j < len(voices):
                        voice = voices[i + j]
                        
                        with cols[j]:
                            with st.container():
                                st.markdown(f"""
                                <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px;">
                                    <h4>{voice['name']}</h4>
                                    <p><strong>Gender:</strong> {voice['gender']}</p>
                                    <p><strong>Style:</strong> {voice['style']}</p>
                                    <p><strong>Language:</strong> {voice['language']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Preview button
                                if st.button("Preview", key=f"preview_{voice['id']}"):
                                    sample_text = "This is a sample of my voice. How do I sound to you?"
                                    
                                    # Simulate audio preview
                                    with st.spinner("Generating voice preview..."):
                                        time.sleep(1)
                                        
                                        # Voice preview would go here
                                        # In a real implementation, this would play an audio sample
                                        st.info(f"Preview of '{voice['name']}' voice: \"{sample_text}\"")
                                        st.markdown("*Audio preview would play here in a real implementation*")
                                
                                # Use this voice button
                                if st.button("Use This Voice", key=f"use_{voice['id']}"):
                                    # Show character selection for the script
                                    st.session_state.selected_voice_id = voice['id']
                                    st.session_state.selected_voice_name = voice['name']
                                    st.session_state.show_character_selection = True
                                    st.experimental_rerun()
        else:
            st.warning("No voices match your filter criteria. Please adjust your filters.")
        
        # Custom voice upload
        st.markdown("### Upload Custom Voice Sample")
        uploaded_voice = st.file_uploader("Upload a voice sample (WAV or MP3)", type=["wav", "mp3"])
        
        if uploaded_voice is not None:
            # Process uploaded voice sample
            st.success(f"Uploaded voice sample: {uploaded_voice.name}")
            
            voice_name = st.text_input("Voice Name", value="My Custom Voice")
            
            if st.button("Use Custom Voice"):
                # Add custom voice to session state
                custom_voice_id = f"custom_{int(time.time())}"
                
                # Show character selection for the script
                st.session_state.selected_voice_id = custom_voice_id
                st.session_state.selected_voice_name = voice_name
                st.session_state.show_character_selection = True
                st.experimental_rerun()
        
        # Character selection for the script (shown after selecting a voice)
        if 'show_character_selection' in st.session_state and st.session_state.show_character_selection:
            voice_id = st.session_state.selected_voice_id
            voice_name = st.session_state.selected_voice_name
            
            st.markdown(f"### Assign '{voice_name}' to Characters")
            
            # Get all characters from the script
            characters = get_all_characters(st.session_state.scripts[current_project]["scenes"])
            
            # Add narrator as an option
            if "NARRATOR" not in characters:
                characters.append("NARRATOR")
            
            # Character selection
            character_options = characters.copy()
            character_options.insert(0, "All Characters")
            
            selected_character = st.selectbox(
                "Select Character",
                character_options,
                key=f"character_select_{voice_id}"
            )
            
            if st.button("Assign Voice", key=f"assign_{voice_id}"):
                if selected_character == "All Characters":
                    # Assign this voice to all characters
                    for character in characters:
                        st.session_state.audio[current_project]["selected_voices"][character] = {
                            "voice_id": voice_id,
                            "voice_name": voice_name
                        }
                else:
                    # Assign this voice to the selected character
                    st.session_state.audio[current_project]["selected_voices"][selected_character] = {
                        "voice_id": voice_id,
                        "voice_name": voice_name
                    }
                
                st.success(f"Voice '{voice_name}' assigned to {selected_character if selected_character != 'All Characters' else 'all characters'}!")
                st.session_state.show_character_selection = False
                st.experimental_rerun()
        
        # Display current voice assignments
        st.markdown("### Current Voice Assignments")
        
        voice_assignments = st.session_state.audio[current_project]["selected_voices"]
        
        if voice_assignments:
            for character, voice_data in voice_assignments.items():
                st.markdown(f"**{character}**: {voice_data['voice_name']}")
                
                if st.button("Remove", key=f"remove_{character}"):
                    del st.session_state.audio[current_project]["selected_voices"][character]
                    st.experimental_rerun()
        else:
            st.info("No voices assigned yet. Select voices from the catalog above.")
    
    with tabs[1]:
        st.subheader("Audio Generation")
        
        # Get scenes from script
        scenes = st.session_state.scripts[current_project]["scenes"]
        
        # Check if voices have been assigned
        if not st.session_state.audio[current_project]["selected_voices"]:
            st.warning("Please assign voices to characters in the Voice Selection tab first.")
            return
        
        # Generate all button
        if st.button("Generate Audio for All Scenes", type="primary"):
            with st.spinner("Generating audio for all scenes..."):
                # Simulate API call with progress
                progress_bar = st.progress(0)
                
                # Generate audio for each scene
                for i, scene in enumerate(scenes):
                    scene_id = f"scene_{i+1}"
                    
                    # Update progress
                    progress = int((i / len(scenes)) * 100)
                    progress_bar.progress(progress)
                    time.sleep(0.5)  # Simulate processing time
                    
                    # Get dialogue lines
                    if "dialogue" in scene and scene["dialogue"]:
                        dialogue_lines = scene["dialogue"]
                        
                        # Generate audio for each dialogue line
                        for j, line in enumerate(dialogue_lines):
                            character = line["character"]
                            text = line["text"]
                            
                            # Get assigned voice for this character (use NARRATOR as fallback)
                            voice_data = st.session_state.audio[current_project]["selected_voices"].get(
                                character, 
                                st.session_state.audio[current_project]["selected_voices"].get("NARRATOR", None)
                            )
                            
                            if voice_data:
                                # Generate mock audio
                                audio_url = generate_mock_audio(text, voice_data["voice_id"])
                                
                                # Save generated audio
                                audio_id = f"{scene_id}_line_{j+1}"
                                st.session_state.audio[current_project]["generated_audio"][audio_id] = {
                                    "url": audio_url,
                                    "text": text,
                                    "character": character,
                                    "voice_id": voice_data["voice_id"],
                                    "voice_name": voice_data["voice_name"],
                                    "duration": get_mock_audio_duration(text)
                                }
                    
                    # Generate narration if no dialogue
                    else:
                        # Get content as narration
                        narration_text = scene["content"]
                        
                        # Get assigned voice for narrator
                        voice_data = st.session_state.audio[current_project]["selected_voices"].get("NARRATOR")
                        
                        if voice_data:
                            # Generate mock audio
                            audio_url = generate_mock_audio(narration_text, voice_data["voice_id"])
                            
                            # Save generated audio
                            audio_id = f"{scene_id}_narration"
                            st.session_state.audio[current_project]["generated_audio"][audio_id] = {
                                "url": audio_url,
                                "text": narration_text,
                                "character": "NARRATOR",
                                "voice_id": voice_data["voice_id"],
                                "voice_name": voice_data["voice_name"],
                                "duration": get_mock_audio_duration(narration_text)
                            }
                
                # Complete progress
                progress_bar.progress(100)
                
                # Mark audio as complete
                st.session_state.projects[current_project]["progress"]["audio"] = True
                
                st.success("Audio generated for all scenes!")
        
        # Audio preview section
        st.subheader("Audio Preview")
        
        if st.session_state.audio[current_project]["generated_audio"]:
            # Get all generated audio clips
            audio_clips = st.session_state.audio[current_project]["generated_audio"]
            
            # Group clips by scene
            scene_clips = {}
            for audio_id, audio_data in audio_clips.items():
                scene_id = audio_id.split("_line_")[0] if "_line_" in audio_id else audio_id.split("_narration")[0]
                
                if scene_id not in scene_clips:
                    scene_clips[scene_id] = []
                
                scene_clips[scene_id].append({
                    "audio_id": audio_id,
                    "data": audio_data
                })
            
            # Display clips by scene
            for scene_id, clips in scene_clips.items():
                scene_index = int(scene_id.split("_")[1]) - 1
                
                with st.expander(f"Scene {scene_index + 1} Audio"):
                    for clip in clips:
                        audio_id = clip["audio_id"]
                        audio_data = clip["data"]
                        
                        st.markdown(f"**{audio_data['character']}** (Voice: {audio_data['voice_name']})")
                        st.markdown(f"*\"{audio_data['text']}\"*")
                        st.markdown(f"Duration: {audio_data['duration']:.1f} seconds")
                        
                        # Audio player would go here in a real implementation
                        st.markdown("*Audio player would appear here in a real implementation*")
                        
                        # Regenerate button
                        if st.button("Regenerate", key=f"regen_audio_{audio_id}"):
                            with st.spinner("Regenerating audio..."):
                                time.sleep(1)
                                
                                # Generate new mock audio
                                new_audio_url = generate_mock_audio(
                                    audio_data["text"],
                                    audio_data["voice_id"],
                                    is_regeneration=True
                                )
                                
                                # Update audio
                                st.session_state.audio[current_project]["generated_audio"][audio_id]["url"] = new_audio_url
                                
                                st.success("Audio regenerated!")
                        
                        st.markdown("---")
        else:
            st.info("No audio generated yet. Click 'Generate Audio for All Scenes' to create audio.")
    
    with tabs[2]:
        st.subheader("Audio Settings")
        
        # Audio settings
        audio_settings = st.session_state.audio[current_project]["audio_settings"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Voice volume
            voice_volume = st.slider(
                "Voice Volume",
                min_value=0.0,
                max_value=1.0,
                value=audio_settings["volume"],
                step=0.1,
                format="%.1f"
            )
            
            # Speech speed
            speech_speed = st.slider(
                "Speech Speed",
                min_value=0.5,
                max_value=2.0,
                value=audio_settings["speed"],
                step=0.1,
                format="%.1f"
            )
        
        with col2:
            # Background music option
            add_bg_music = st.checkbox(
                "Add Background Music",
                value=audio_settings["add_background_music"]
            )
            
            # Background music volume (only shown if background music is enabled)
            bg_music_volume = 0.2
            if add_bg_music:
                bg_music_volume = st.slider(
                    "Background Music Volume",
                    min_value=0.0,
                    max_value=1.0,
                    value=audio_settings["background_music_volume"],
                    step=0.1,
                    format="%.1f"
                )
        
        # Background music selection (only shown if background music is enabled)
        if add_bg_music:
            st.subheader("Background Music")
            
            # Music categories
            music_category = st.selectbox(
                "Music Category",
                ["Upbeat", "Corporate", "Inspirational", "Cinematic", "Relaxing", "Technology"]
            )
            
            # Display music options based on category
            music_options = get_background_music(music_category)
            
            for i, music in enumerate(music_options):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{music['title']}** ({music['duration']})")
                    st.markdown(f"*{music['description']}*")
                
                with col2:
                    # Preview button
                    if st.button("Preview", key=f"preview_music_{i}"):
                        st.info(f"Preview for '{music['title']}' would play here in a real implementation")
                    
                    # Select button
                    if st.button("Select", key=f"select_music_{i}"):
                        st.session_state.audio[current_project]["background_music"] = music
                        st.success(f"Background music set to '{music['title']}'")
            
            # Display selected background music
            if st.session_state.audio[current_project]["background_music"]:
                music = st.session_state.audio[current_project]["background_music"]
                
                st.markdown("### Selected Background Music")
                st.markdown(f"**{music['title']}** ({music['duration']})")
                
                # Remove button
                if st.button("Remove Background Music"):
                    st.session_state.audio[current_project]["background_music"] = None
                    st.success("Background music removed")
        
        # Save settings button
        if st.button("Save Audio Settings", type="primary"):
            # Update settings in session state
            st.session_state.audio[current_project]["audio_settings"] = {
                "volume": voice_volume,
                "speed": speech_speed,
                "add_background_music": add_bg_music,
                "background_music_volume": bg_music_volume if add_bg_music else 0.2
            }
            
            st.success("Audio settings saved!")
    
    # Continue button (only if audio is generated)
    if st.session_state.audio[current_project]["generated_audio"]:
        if st.button("Continue to Video Production", type="primary"):
            st.session_state.current_step = 4
            st.experimental_rerun()

#################################################
# VIDEO PRODUCTION MODULE
#################################################

def get_avatar_catalog():
    """Get avatar catalog
    
    Returns:
        list: List of avatar dictionaries
    """
    # Mock avatar catalog
    avatars = [
        {
            "id": "avatar_1",
            "name": "Alex",
            "style": "Professional",
            "gender": "Male",
            "thumbnail": "https://via.placeholder.com/200x200?text=Alex",
            "preview": "https://via.placeholder.com/400x400?text=Alex+Preview",
            "description": "Professional male presenter with business attire.",
            "best_for": "Corporate videos, explainers, product demos"
        },
        {
            "id": "avatar_2",
            "name": "Sarah",
            "style": "Professional",
            "gender": "Female",
            "thumbnail": "https://via.placeholder.com/200x200?text=Sarah",
            "preview": "https://via.placeholder.com/400x400?text=Sarah+Preview",
            "description": "Professional female presenter with business casual attire.",
            "best_for": "Marketing videos, tutorials, customer testimonials"
        },
        {
            "id": "avatar_3",
            "name": "Max",
            "style": "Casual",
            "gender": "Male",
            "thumbnail": "https://via.placeholder.com/200x200?text=Max",
            "preview": "https://via.placeholder.com/400x400?text=Max+Preview",
            "description": "Casual male presenter with relaxed style.",
            "best_for": "Social media content, casual explainers, youth-oriented content"
        },
        {
            "id": "avatar_4",
            "name": "Jamie",
            "style": "Casual",
            "gender": "Female",
            "thumbnail": "https://via.placeholder.com/200x200?text=Jamie",
            "preview": "https://via.placeholder.com/400x400?text=Jamie+Preview",
            "description": "Casual female presenter with modern style.",
            "best_for": "Lifestyle content, social media, vlogs"
        },
        {
            "id": "avatar_5",
            "name": "Dr. Chen",
            "style": "Technical",
            "gender": "Male",
            "thumbnail": "https://via.placeholder.com/200x200?text=Dr.+Chen",
            "preview": "https://via.placeholder.com/400x400?text=Dr.+Chen+Preview",
            "description": "Technical male presenter with professional appearance.",
            "best_for": "Technical presentations, educational content, research"
        },
        {
            "id": "avatar_6",
            "name": "Prof. Davis",
            "style": "Technical",
            "gender": "Female",
            "thumbnail": "https://via.placeholder.com/200x200?text=Prof.+Davis",
            "preview": "https://via.placeholder.com/400x400?text=Prof.+Davis+Preview",
            "description": "Technical female presenter with academic style.",
            "best_for": "Educational videos, technical explanations, research presentations"
        },
        {
            "id": "avatar_7",
            "name": "Jordan",
            "style": "Modern",
            "gender": "Neutral",
            "thumbnail": "https://via.placeholder.com/200x200?text=Jordan",
            "preview": "https://via.placeholder.com/400x400?text=Jordan+Preview",
            "description": "Modern presenter with neutral gender presentation.",
            "best_for": "Contemporary content, inclusive messaging, diverse audiences"
        },
        {
            "id": "avatar_8",
            "name": "Virtual Assistant",
            "style": "Digital",
            "gender": "Neutral",
            "thumbnail": "https://via.placeholder.com/200x200?text=Virtual+Assistant",
            "preview": "https://via.placeholder.com/400x400?text=Virtual+Assistant+Preview",
            "description": "Digital assistant character with high-tech appearance.",
            "best_for": "Tech products, futuristic presentations, digital services"
        }
    ]
    
    return avatars
            <div class="step-circle completed">1</div>
            <div>Content</div>
        </div>
        <div class="progress-step">
            <div class="step-circle completed">2</div>
            <div>Visual</div>
        </div>
        <div class="progress-step">
            <div class="step-circle active">3</div>
            <div>Audio</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">4</div>
            <div>Video</div>
        </div>
        <div class="progress-step">                        # Generate mock response based on input
                        if "shorter" in user_input.lower():
                            ai_response = "I've shortened the script while maintaining the key messages. Would you like me to focus on any specific section?"
                        elif "longer" in user_input.lower():
                            ai_response = "I've expanded the script with more details and descriptions. Let me know if you want me to elaborate on any particular part."
                        elif "tone" in user_input.lower():
                            ai_response = "I've adjusted the tone as requested. The script now has a more conversational and engaging style."
                        elif "call to action" in user_input.lower():
                            ai_response = "I've strengthened the call to action at the end of the script to be more compelling and direct."
                        else:
                            ai_response = "I've made the suggested changes to your script. Is there anything specific you'd like me to help with next?"
                    
                    # Add AI response to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })
                    
                    # Clear input
                    st.session_state.chat_input = ""
                    
                    # Rerun to update chat display
                    st.experimental_rerun()
            
            # Script editor
            st.subheader("Edit Script")
            script_content = st.text_area(
                "Script Content",
                value=st.session_state.scripts[current_project]["content"],
                height=400,
                key="script_editor"
            )
            
            if st.button("Save Changes", key="save_script"):
                # Save changes to session state
                st.session_state.scripts[current_project]["content"] = script_content
                st.session_state.scripts[current_project]["formatted_content"] = format_script(
                    script_content, 
                    st.session_state.scripts[current_project]["type"]
                )
                
                # Update scenes
                st.session_state.scripts[current_project]["scenes"] = parse_scenes(
                    script_content, 
                    st.session_state.scripts[current_project]["type"]
                )
                
                st.success("Script updated successfully!")
        else:
            st.info("Generate a script first to use the editor.")
    
    with tabs[2]:
        st.subheader("Script Preview")
        
        if st.session_state.scripts[current_project]["formatted_content"]:
            # Display formatted script
            st.markdown("### Formatted Script")
            st.markdown(st.session_state.scripts[current_project]["formatted_content"], unsafe_allow_html=True)
            
            # Scene breakdown
            st.subheader("Scene Breakdown")
            scenes = st.session_state.scripts[current_project]["scenes"]
            
            for i, scene in enumerate(scenes):
                with st.expander(f"Scene {i+1}: {scene['heading']}"):
                    st.markdown(f"**Type:** {scene['type']}")
                    st.markdown(f"**Content:** {scene['content']}")
                    
                    if "dialogue" in scene and scene["dialogue"]:
                        st.markdown("**Dialogue:**")
                        for line in scene["dialogue"]:
                            st.markdown(f"- **{line['character']}:** {line['text']}")
            
            # Continue button
            if st.button("Continue to Visual Assets", type="primary"):
                st.session_state.current_step = 2
                st.experimental_rerun()
        else:
            st.info("Generate a script first to see the preview.")

#################################################
# VISUAL ASSET CREATION MODULE
#################################################

def get_style_preview(style):
    """Get a preview image URL for the selected style
    
    Args:
        style: Selected style name
        
    Returns:
        str: URL to a preview image
    """
    # Mock image URLs for different styles
    style_previews = {
        "realistic": "https://via.placeholder.com/600x400?text=Realistic+Style",
        "3d animation": "https://via.placeholder.com/600x400?text=3D+Animation+Style",
        "2d animation": "https://via.placeholder.com/600x400?text=2D+Animation+Style",
        "cartoon": "https://via.placeholder.com/600x400?text=Cartoon+Style",
        "cinematic": "https://via.placeholder.com/600x400?text=Cinematic+Style",
        "minimalist": "https://via.placeholder.com/600x400?text=Minimalist+Style"
    }
    
    return style_previews.get(style.lower(), "https://via.placeholder.com/600x400?text=Preview+Not+Available")

def get_style_description(style):
    """Get a description for the selected style
    
    Args:
        style: Selected style name
        
    Returns:
        str: Description of the style
    """
    style_descriptions = {
        "realistic": "Photorealistic images with natural lighting, textures, and colors. Perfect for product demos and professional marketing videos.",
        "3d animation": "Modern 3D rendered visuals with depth and dimension. Great for explaining complex concepts or products.",
        "2d animation": "Flat design with vibrant colors and smooth animations. Ideal for explainer videos and engaging content.",
        "cartoon": "Playful, exaggerated style with bold outlines and vibrant colors. Excellent for light-hearted and engaging content.",
        "cinematic": "Film-like quality with dramatic lighting, composition, and color grading. Perfect for storytelling and emotional impact.",
        "minimalist": "Clean, simple designs with limited color palette and essential elements only. Great for focusing on key messages."
    }
    
    return style_descriptions.get(style.lower(), "No description available for this style.")

def generate_image_prompt(scene):
    """Generate an image prompt based on scene content
    
    Args:
        scene: Scene dictionary
        
    Returns:
        str: Generated image prompt
    """
    # Extract scene content and heading
    heading = scene["heading"]
    content = scene["content"]
    
    # Create a basic prompt based on scene content
    if "EXT." in heading or "INT." in heading:
        # For screenplay format
        location = heading.split("-")[0].strip()
        prompt = f"{location}: {content}"
    else:
        # For other formats
        prompt = f"{heading}: {content}"
        
        # Add dialogue context if available
        if "dialogue" in scene and scene["dialogue"]:
            dialogue_context = " ".join([line["text"] for line in scene["dialogue"][:2]])
            prompt += f" Context from dialogue: {dialogue_context}"
    
    return prompt

def generate_mock_image(prompt, style, aspect_ratio, is_regeneration=False):
    """Generate a mock image based on inputs
    
    Args:
        prompt: Image prompt
        style: Visual style
        aspect_ratio: Aspect ratio
        is_regeneration: Whether this is a regeneration
        
    Returns:
        str: URL to the generated image
    """
    # Extract dimensions from aspect ratio
    if "16:9" in aspect_ratio:
        width, height = 800, 450
    elif "1:1" in aspect_ratio:
        width, height = 600, 600
    elif "9:16" in aspect_ratio:
        width, height = 450, 800
    else:
        width, height = 800, 600
    
    # Generate a mock image URL with a random ID to simulate different images
    random_id = random.randint(1, 1000)
    seed = random_id + (500 if is_regeneration else 0)  # Different seed for regeneration
    
    # Format the prompt for URL
    short_prompt = prompt[:50].replace(" ", "+")
    
    # Create different colored backgrounds based on style
    style_colors = {
        "realistic": "8B4513",  # Brown
        "3d animation": "4682B4",  # Steel Blue
        "2d animation": "32CD32",  # Lime
        "cartoon": "FF6347",  # Tomato
        "cinematic": "483D8B",  # Dark Slate Blue
        "minimalist": "F5F5F5"   # White Smoke
    }
    
    color = style_colors.get(style.lower(), "CCCCCC")
    
    # Create a URL for a placeholder image
    image_url = f"https://via.placeholder.com/{width}x{height}/{color}?text={short_prompt}&seed={seed}"
    
    return image_url

def show_visual_asset_creation():
    """Visual Asset Creation page"""
    st.title("Visual Asset Creation")
    
    # Progress indicator
    st.markdown("""
    <div class="progress-indicator">
        <div class="progress-step">
            <div class="step-circle completed">1</div>
            <div>Content</div>
        </div>
        <div class="progress-step">
            <div class="step-circle active">2</div>
            <div>Visual</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">3</div>
            <div>Audio</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">4</div>
            <div>Video</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">5</div>
            <div>Export</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    current_project = st.session_state.current_project
    
    # Check if script exists
    if current_project not in st.session_state.scripts or not st.session_state.scripts[current_project]["scenes"]:
        st.warning("Please create a script first in the Content Generation section.")
        if st.button("Go to Content Generation"):
            st.session_state.current_step = 1
            st.experimental_rerun()
        return
    
    # Initialize images in session if not existing
    if current_project not in st.session_state.images:
        st.session_state.images[current_project] = {
            "style": "realistic",
            "generated_images": {},
            "custom_images": {}
        }
    
    # Visual asset tabs
    tabs = st.tabs(["Style Selection", "Scene Images", "Asset Manager"])
    
    with tabs[0]:
        st.subheader("Visual Style Selection")
        
        # Style selection
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_style = st.radio(
                "Choose Visual Style",
                ["Realistic", "3D Animation", "2D Animation", "Cartoon", "Cinematic", "Minimalist"],
                index=0,  # Default to Realistic
                key="style_selector"
            )
            
            if st.button("Apply Style", key="apply_style"):
                st.session_state.images[current_project]["style"] = selected_style.lower()
                st.success(f"Applied style: {selected_style}")
        
        with col2:
            # Style preview
            st.markdown(f"### {selected_style} Style Preview")
            
            # Generate mock preview based on selected style
            preview_url = get_style_preview(selected_style.lower())
            st.image(preview_url, caption=f"{selected_style} Style Example", use_column_width=True)
            
            st.markdown(f"""
            **{selected_style} Style Characteristics:**
            
            {get_style_description(selected_style.lower())}
            """)
    
    with tabs[1]:
        st.subheader("Scene Images Generator")
        
        # Get scenes from script
        scenes = st.session_state.scripts[current_project]["scenes"]
        
        # Create tabs for each scene
        scene_tabs = st.tabs([f"Scene {i+1}" for i in range(len(scenes))])
        
        for i, (scene_tab, scene) in enumerate(zip(scene_tabs, scenes)):
            with scene_tab:
                scene_id = f"scene_{i+1}"
                
                # Scene content display
                st.markdown(f"### {scene['heading']}")
                st.markdown(f"**Content:** {scene['content']}")
                
                if "dialogue" in scene and scene["dialogue"]:
                    dialogue_text = "\n".join([f"**{line['character']}**: {line['text']}" for line in scene["dialogue"]])
                    st.markdown(f"**Dialogue:**\n{dialogue_text}")
                
                # Image prompt customization
                st.subheader("Image Generation")
                
                # Default image prompt based on scene
                default_prompt = generate_image_prompt(scene)
                
                image_prompt = st.text_area(
                    "Image Prompt",
                    value=default_prompt,
                    height=100,
                    key=f"prompt_{scene_id}"
                )
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Additional parameters
                    aspect_ratio = st.selectbox(
                        "Aspect Ratio",
                        ["16:9 (Landscape)", "1:1 (Square)", "9:16 (Portrait/Mobile)"],
                        key=f"aspect_{scene_id}"
                    )
                
                with col2:
                    quality = st.select_slider(
                        "Quality",
                        options=["Standard", "High", "Premium"],
                        value="High",
                        key=f"quality_{scene_id}"
                    )
                
                # Generate button
                if st.button("Generate Image", key=f"generate_{scene_id}"):
                    with st.spinner("Generating image..."):
                        # Simulate API call with progress
                        progress_bar = st.progress(0)
                        for i in range(100):
                            time.sleep(0.02)
                            progress_bar.progress(i + 1)
                        
                        # Generate mock image
                        generated_image = generate_mock_image(
                            image_prompt,
                            st.session_state.images[current_project]["style"],
                            aspect_ratio
                        )
                        
                        # Save generated image
                        st.session_state.images[current_project]["generated_images"][scene_id] = {
                            "url": generated_image,
                            "prompt": image_prompt,
                            "style": st.session_state.images[current_project]["style"],
                            "aspect_ratio": aspect_ratio,
                            "quality": quality
                        }
                
                # Display generated image if exists
                if scene_id in st.session_state.images[current_project]["generated_images"]:
                    image_data = st.session_state.images[current_project]["generated_images"][scene_id]
                    
                    st.subheader("Generated Image")
                    st.image(
                        image_data["url"],
                        caption=f"Generated image for {scene['heading']}",
                        use_column_width=True
                    )
                    
                    # Regeneration options
                    if st.button("Regenerate", key=f"regenerate_{scene_id}"):
                        with st.spinner("Regenerating image..."):
                            # Simulate API call with progress
                            progress_bar = st.progress(0)
                            for i in range(100):
                                time.sleep(0.02)
                                progress_bar.progress(i + 1)
                            
                            # Generate a different mock image
                            regenerated_image = generate_mock_image(
                                image_prompt,
                                st.session_state.images[current_project]["style"],
                                aspect_ratio,
                                is_regeneration=True
                            )
                            
                            # Update generated image
                            st.session_state.images[current_project]["generated_images"][scene_id]["url"] = regenerated_image
                            st.experimental_rerun()
                
                # Upload custom image option
                st.subheader("Upload Custom Image")
                uploaded_file = st.file_uploader(
                    "Upload an image for this scene", 
                    type=["jpg", "jpeg", "png"],
                    key=f"upload_{scene_id}"
                )
                
                if uploaded_file is not None:
                    # Process uploaded image
                    image = Image.open(uploaded_file)
                    
                    # Convert to bytes for storage
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    image_bytes = buf.getvalue()
                    
                    # Create a data URI
                    encoded = base64.b64encode(image_bytes).decode()
                    data_uri = f"data:image/png;base64,{encoded}"
                    
                    # Save uploaded image
                    st.session_state.images[current_project]["custom_images"][scene_id] = {
                        "url": data_uri,
                        "filename": uploaded_file.name
                    }
                    
                    st.success(f"Uploaded image: {uploaded_file.name}")
                
                # Display custom image if exists
                if scene_id in st.session_state.images[current_project]["custom_images"]:
                    image_data = st.session_state.images[current_project]["custom_images"][scene_id]
                    
                    st.subheader("Custom Image")
                    st.image(
                        image_data["url"],
                        caption=f"Custom image: {image_data['filename']}",
                        use_column_width=True
                    )
    
    with tabs[2]:
        st.subheader("Asset Manager")
        
        # Count generated and custom images
        generated_count = len(st.session_state.images[current_project]["generated_images"])
        custom_count = len(st.session_state.images[current_project]["custom_images"])
        
        # Asset overview
        st.markdown(f"""
        ### Asset Overview
        
        - **Total Scenes:** {len(scenes)}
        - **Generated Images:** {generated_count}/{len(scenes)}
        - **Custom Uploaded Images:** {custom_count}
        - **Current Style:** {st.session_state.images[current_project]["style"].title()}
        """)
        
        # Generated images gallery
        if generated_count > 0:
            st.subheader("Generated Images Gallery")
            
            # Create a grid of images
            cols = st.columns(3)
            
            for idx, (scene_id, image_data) in enumerate(st.session_state.images[current_project]["generated_images"].items()):
                col_idx = idx % 3
                
                with cols[col_idx]:
                    st.image(
                        image_data["url"],
                        caption=f"Scene {scene_id.split('_')[1]}",
                        use_column_width=True
                    )
                    
                    # Image actions
                    if st.button("Delete", key=f"delete_gen_{scene_id}"):
                        # Remove image from session state
                        del st.session_state.images[current_project]["generated_images"][scene_id]
                        st.experimental_rerun()
        
        # Custom images gallery
        if custom_count > 0:
            st.subheader("Custom Images Gallery")
            
            # Create a grid of images
            cols = st.columns(3)
            
            for idx, (scene_id, image_data) in enumerate(st.session_state.images[current_project]["custom_images"].items()):
                col_idx = idx % 3
                
                with cols[col_idx]:
                    st.image(
                        image_data["url"],
                        caption=f"{image_data['filename']}",
                        use_column_width=True
                    )
                    
                    # Image actions
                    if st.button("Delete", key=f"delete_custom_{scene_id}"):
                        # Remove image from session state
                        del st.session_state.images[current_project]["custom_images"][scene_id]
                        st.experimental_rerun()
        
        # Generate all missing images
        if generated_count < len(scenes):
            if st.button("Generate All Missing Images", type="primary"):
                with st.spinner("Generating images..."):
                    # Simulate API call with progress
                    progress_bar = st.progress(0)
                    
                    # Find missing scenes
                    missing_scenes = []
                    for i, scene in enumerate(scenes):
                        scene_id = f"scene_{i+1}"
                        if scene_id not in st.session_state.images[current_project]["generated_images"]:
                            missing_scenes.append((scene_id, scene))
                    
                    # Generate images for missing scenes
                    for idx, (scene_id, scene) in enumerate(missing_scenes):
                        # Update progress
                        progress = int((idx / len(missing_scenes)) * 100)
                        progress_bar.progress(progress)
                        time.sleep(0.5)  # Simulate processing time
                        
                        # Generate mock image
                        image_prompt = generate_image_prompt(scene)
                        generated_image = generate_mock_image(
                            image_prompt,
                            st.session_state.images[current_project]["style"],
                            "16:9 (Landscape)"  # Default aspect ratio
                        )
                        
                        # Save generated image
                        st.session_state.images[current_project]["generated_images"][scene_id] = {
                            "url": generated_image,
                            "prompt": image_prompt,
                            "style": st.session_state.images[current_project]["style"],
                            "aspect_ratio": "16:9 (Landscape)",
                            "quality": "High"
                        }
                    
                    # Complete progress
                    progress_bar.progress(100)
                    
                    # Mark visual assets as complete
                    st.session_state.projects[current_project]["progress"]["visual_assets"] = True
                    
                    st.success("All images generated successfully!")
        
        # Regenerate all images
        if generated_count > 0:
            if st.button("Regenerate All Images"):
                with st.spinner("Regenerating images..."):
                    # Simulate API call with progress
                    progress_bar = st.progress(0)
                    
                    # Regenerate all images
                    scene_ids = list(st.session_state.images[current_project]["generated_images"].keys())
                    
                    for idx, scene_id in enumerate(scene_ids):
                        # Update progress
                        progress = int((idx / len(scene_ids)) * 100)
                        progress_bar.progress(progress)
                        time.sleep(0.5)  # Simulate processing time
                        
                        # Get current image data
                        image_data = st.session_state.images[current_project]["generated_images"][scene_id]
                        
                        # Generate a different mock image
                        regenerated_image = generate_mock_image(
                            image_data["prompt"],
                            image_data["style"],
                            image_data["aspect_ratio"],
                            is_regeneration=True
                        )
                        
                        # Update generated image
                        st.session_state.images[current_project]["generated_images"][scene_id]["url"] = regenerated_image
                    
                    # Complete progress
                    progress_bar.progress(100)
                    
                    st.success("All images regenerated successfully!")
    
    # Continue to next step button (only if some images exist)
    if generated_count > 0 or custom_count > 0:
        if st.button("Continue to Voice & Audio", type="primary"):
            # Mark visual assets as complete
            st.session_state.projects[current_project]["progress"]["visual_assets"] = True
            
            # Move to next step
            st.session_state.current_step = 3
            st.experimental_rerun()import streamlit as st
import time
from datetime import datetime
import json
import random
import os
import base64
from PIL import Image
import io

# Set page config
st.set_page_config(
    page_title="AI Creative Suite",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

#################################################
# CUSTOM CSS AND STYLING
#################################################

def load_css():
    """Load custom CSS for styling"""
    st.markdown("""
    <style>
        /* Main colors */
        :root {
            --primary-color: #4da6ff;
            --secondary-color: #f0f8ff;
            --text-color: #333333;
            --background-color: #ffffff;
            --accent-color: #ff6b6b;
        }
        
        /* Card styling */
        .stCard {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin-bottom: 1rem;
            background-color: var(--background-color);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stCard:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Button styling */
        .stButton>button {
            background-color: var(--primary-color);
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5rem 1rem;
            transition: background-color 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #3d8bff;
        }
        
        /* Progress indicators */
        .progress-indicator {
            display: flex;
            justify-content: space-between;
            margin-bottom: 2rem;
        }
        
        .progress-step {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .step-circle {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background-color: #e0e0e0;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .step-circle.active {
            background-color: var(--primary-color);
            color: white;
        }
        
        .step-circle.completed {
            background-color: #4CAF50;
            color: white;
        }
        
        /* Custom header */
        .custom-header {
            background-color: var(--primary-color);
            color: white;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 2rem;
        }
        
        /* Preview container */
        .preview-container {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 1rem;
            margin-top: 1rem;
        }
        
        /* Status messages */
        .status-success {
            background-color: #d4edda;
            color: #155724;
            padding: 0.75rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        
        .status-error {
            background-color: #f8d7da;
            color: #721c24;
            padding: 0.75rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        
        .status-info {
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 0.75rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

#################################################
# SESSION STATE MANAGEMENT
#################################################

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    if 'projects' not in st.session_state:
        st.session_state.projects = {}
    
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    
    if 'scripts' not in st.session_state:
        st.session_state.scripts = {}
    
    if 'images' not in st.session_state:
        st.session_state.images = {}
    
    if 'audio' not in st.session_state:
        st.session_state.audio = {}
    
    if 'videos' not in st.session_state:
        st.session_state.videos = {}
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

#################################################
# SIDEBAR AND NAVIGATION
#################################################

def create_sidebar():
    """Create sidebar navigation"""
    with st.sidebar:
        st.image("https://via.placeholder.com/150x100?text=AI+Creative+Suite", use_column_width=True)
        st.title("AI Creative Suite")
        
        # Project selection section
        st.subheader("Project Management")
        
        # Display current project if exists
        if st.session_state.current_project:
            st.info(f"Current Project: {st.session_state.current_project}")
        
        # Project creation and selection
        with st.expander("Projects", expanded=True):
            create_new = st.button("Create New Project")
            
            if create_new:
                st.session_state.show_project_creation = True
            
            if st.session_state.projects:
                project_names = list(st.session_state.projects.keys())
                selected_project = st.selectbox("Select Project", project_names)
                
                if st.button("Load Project"):
                    st.session_state.current_project = selected_project
                    st.success(f"Loaded project: {selected_project}")
                    # Reset step to 1 when loading a new project
                    st.session_state.current_step = 1
                    st.experimental_rerun()
        
        # Workflow navigation (only shown if project is selected)
        if st.session_state.current_project:
            st.subheader("Workflow")
            
            workflow_steps = [
                "Content Generation",
                "Visual Asset Creation",
                "Voice & Audio",
                "Video Production",
                "Export & Share"
            ]
            
            for i, step in enumerate(workflow_steps, 1):
                btn_class = "primary" if i == st.session_state.current_step else "secondary"
                if st.button(f"{i}. {step}", key=f"step_{i}", type=btn_class):
                    st.session_state.current_step = i
                    st.experimental_rerun()
            
            # Display progress
            progress_value = (st.session_state.current_step - 1) / 4
            st.progress(progress_value)
            
            # If project has data, show export options
            if st.session_state.current_project in st.session_state.videos:
                st.subheader("Export Options")
                st.button("Download Video")
                st.button("Share Project")

def show_project_creation():
    """Show project creation dialog"""
    with st.form("project_creation"):
        st.subheader("Create New Project")
        project_name = st.text_input("Project Name")
        project_description = st.text_area("Project Description")
        
        # Project type selection
        project_type = st.selectbox(
            "Project Type",
            [
                "Marketing Video",
                "Explainer Video",
                "Social Media Ad",
                "Product Demo",
                "Creative Storytelling",
                "Other"
            ]
        )
        
        # Target platforms
        target_platforms = st.multiselect(
            "Target Platforms",
            [
                "YouTube",
                "Instagram",
                "Facebook",
                "TikTok",
                "LinkedIn",
                "Twitter",
                "Website",
                "Other"
            ]
        )
        
        # Aspect ratio
        aspect_ratio = st.selectbox(
            "Aspect Ratio",
            [
                "16:9 (Landscape)",
                "1:1 (Square)",
                "9:16 (Portrait/Mobile)",
                "4:3 (Traditional)",
                "2.35:1 (Cinematic)"
            ]
        )
        
        # Project workflow
        workflow = st.selectbox(
            "Project Workflow",
            [
                "Complete Pipeline (Script to Video)",
                "Script to Audio",
                "Existing Script to Video",
                "Existing Assets to Video"
            ]
        )
        
        submitted = st.form_submit_button("Create Project")
        
        if submitted and project_name:
            # Create project structure
            st.session_state.projects[project_name] = {
                "name": project_name,
                "description": project_description,
                "type": project_type,
                "target_platforms": target_platforms,
                "aspect_ratio": aspect_ratio,
                "workflow": workflow,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "progress": {
                    "content_generation": False,
                    "visual_assets": False,
                    "audio": False,
                    "video_production": False
                }
            }
            
            # Set as current project
            st.session_state.current_project = project_name
            st.session_state.show_project_creation = False
            st.success(f"Project '{project_name}' created successfully!")
            st.experimental_rerun()

#################################################
# CONTENT GENERATION MODULE
#################################################

def generate_marketing_script(title, target_audience, tone, duration, key_points):
    """Generate a marketing script based on input parameters
    
    Args:
        title: Title of the video
        target_audience: Target audience description
        tone: Tone of the script
        duration: Duration in seconds
        key_points: List of key points to include
        
    Returns:
        str: Generated script content
    """
    # Create a mock marketing script based on inputs
    intro = f"SCENE 1 - INTRODUCTION\n\nNARRATOR (Voice Over):\nAre you tired of {key_points[0] if key_points else 'the same old solutions'}? Introducing {title}.\n\n"
    
    body = "SCENE 2 - FEATURES AND BENEFITS\n\n"
    for i, point in enumerate(key_points[:3]):
        body += f"VISUAL {i+1}:\n\nNARRATOR (Voice Over):\n{point}\n\n"
    
    if not key_points:
        body += "VISUAL 1:\n\nNARRATOR (Voice Over):\nOur solution offers unparalleled quality and reliability.\n\n"
        body += "VISUAL 2:\n\nNARRATOR (Voice Over):\nCustomers report 95% satisfaction after switching to our service.\n\n"
    
    testimonial = "SCENE 3 - TESTIMONIAL\n\nCUSTOMER (On Screen):\nSince using this product, my business has grown by 200%. I couldn't be happier.\n\n"
    
    closing = "SCENE 4 - CALL TO ACTION\n\nNARRATOR (Voice Over):\nDon't wait any longer. Visit our website or call us today to get started.\n\n"
    
    return intro + body + testimonial + closing

def generate_creative_screenplay(title, tone, duration, key_points):
    """Generate a creative screenplay based on input parameters
    
    Args:
        title: Title of the video
        tone: Tone of the script
        duration: Duration in seconds
        key_points: List of key points to include
        
    Returns:
        str: Generated screenplay content
    """
    # Create a mock creative screenplay based on inputs
    scene1 = f"EXT. CITY STREET - DAY\n\nA bustling city street. People rushing past each other, everyone in their own world.\n\n"
    
    scene2 = f"JAMES (30s, professional) stops in his tracks, noticing something unusual across the street.\n\n"
    
    scene3 = f"JAMES\n(curious)\nWhat in the world is that?\n\n"
    
    scene4 = f"ANGLE ON: A mysterious {key_points[0] if key_points else 'object'} glowing softly in the window display of an antique shop.\n\n"
    
    scene5 = f"INT. ANTIQUE SHOP - MOMENTS LATER\n\nJames enters the dimly lit shop. Dust particles dance in the beams of light coming through the windows.\n\n"
    
    scene6 = f"SHOPKEEPER (70s, enigmatic)\nI've been waiting for someone to notice it.\n\n"
    
    scene7 = f"JAMES\n(surprised)\nWhat is it exactly?\n\n"
    
    scene8 = f"SHOPKEEPER\nIt's not what it is, but what it represents.\n\n"
    
    return scene1 + scene2 + scene3 + scene4 + scene5 + scene6 + scene7 + scene8

def generate_explainer_script(title, target_audience, tone, duration, key_points):
    """Generate an explainer video script based on input parameters
    
    Args:
        title: Title of the video
        target_audience: Target audience description
        tone: Tone of the script
        duration: Duration in seconds
        key_points: List of key points to include
        
    Returns:
        str: Generated script content
    """
    # Create a mock explainer script based on inputs
    intro = f"SCENE 1 - PROBLEM STATEMENT\n\nVISUAL: Abstract animation showing the problem.\n\nNARRATOR (Voice Over):\nHave you ever wondered about {key_points[0] if key_points else 'this common problem'}? You're not alone.\n\n"
    
    explanation = "SCENE 2 - EXPLANATION\n\nVISUAL: Simple diagram breaking down the concept.\n\nNARRATOR (Voice Over):\nLet's break this down simply.\n\n"
    
    points = ""
    for i, point in enumerate(key_points[:3]):
        points += f"SCENE {i+3} - KEY POINT {i+1}\n\nVISUAL: Illustration of concept {i+1}.\n\nNARRATOR (Voice Over):\n{point}\n\n"
    
    if not key_points:
        points += "SCENE 3 - KEY POINT 1\n\nVISUAL: Illustration of first concept.\n\nNARRATOR (Voice Over):\nFirstly, understanding the basics is essential.\n\n"
        points += "SCENE 4 - KEY POINT 2\n\nVISUAL: Illustration of second concept.\n\nNARRATOR (Voice Over):\nSecondly, application makes all the difference.\n\n"
    
    conclusion = "SCENE 6 - CONCLUSION\n\nVISUAL: Summary animation with key takeaways.\n\nNARRATOR (Voice Over):\nNow you understand the full picture. Remember these key points next time you encounter this situation.\n\n"
    
    return intro + explanation + points + conclusion

def generate_product_demo(title, target_audience, tone, duration, key_points):
    """Generate a product demo script based on input parameters
    
    Args:
        title: Title of the video
        target_audience: Target audience description
        tone: Tone of the script
        duration: Duration in seconds
        key_points: List of key points to include
        
    Returns:
        str: Generated script content
    """
    # Create a mock product demo script based on inputs
    intro = f"SCENE 1 - PRODUCT INTRODUCTION\n\nHOST (On Screen):\nHello everyone! Today I'm excited to show you {title}, the revolutionary product that's changing the way we {key_points[0] if key_points else 'work'}.\n\n"
    
    overview = "SCENE 2 - PRODUCT OVERVIEW\n\nVISUAL: Product from multiple angles.\n\nHOST (Voice Over):\nLet's take a look at what makes this product special.\n\n"
    
    features = ""
    for i, point in enumerate(key_points[:3]):
        features += f"SCENE {i+3} - FEATURE {i+1}\n\nVISUAL: Close-up of feature {i+1}.\n\nHOST (Voice Over):\n{point}\n\n"
    
    if not key_points:
        features += "SCENE 3 - FEATURE 1\n\nVISUAL: Close-up of first feature.\n\nHOST (Voice Over):\nThe intuitive interface makes it accessible to everyone.\n\n"
        features += "SCENE 4 - FEATURE 2\n\nVISUAL: Close-up of second feature.\n\nHOST (Voice Over):\nThe powerful performance sets a new industry standard.\n\n"
    
    demo = "SCENE 6 - LIVE DEMONSTRATION\n\nHOST (On Screen):\nNow let me show you how easy it is to use.\n\n[Host demonstrates the product in real-time]\n\n"
    
    closing = "SCENE 7 - CLOSING\n\nHOST (On Screen):\nAs you can see, it's that simple! Visit our website to learn more and purchase yours today.\n\n"
    
    return intro + overview + features + demo + closing

def format_script(script, script_type):
    """Format the script for display
    
    Args:
        script: Raw script content
        script_type: Type of script
        
    Returns:
        str: Formatted HTML for display
    """
    # Split script into lines
    lines = script.split("\n")
    formatted_lines = []
    
    for line in lines:
        if not line.strip():
            formatted_lines.append("<br>")
        elif line.startswith("SCENE") or line.startswith("EXT.") or line.startswith("INT."):
            formatted_lines.append(f"<h4 style='color: #4da6ff; margin-top: 20px;'>{line}</h4>")
        elif "NARRATOR" in line or "HOST" in line or "CUSTOMER" in line or line.strip().endswith(")"):
            formatted_lines.append(f"<p style='color: #6c757d; font-style: italic;'>{line}</p>")
        elif "VISUAL" in line:
            formatted_lines.append(f"<p style='color: #28a745; font-weight: bold;'>{line}</p>")
        elif line.strip().isupper() and len(line.strip()) > 0:
            formatted_lines.append(f"<p style='font-weight: bold;'>{line}</p>")
        else:
            formatted_lines.append(f"<p>{line}</p>")
    
    return "".join(formatted_lines)

def parse_scenes(script, script_type):
    """Parse the script into scenes
    
    Args:
        script: Raw script content
        script_type: Type of script
        
    Returns:
        list: List of scene dictionaries
    """
    lines = script.split("\n")
    scenes = []
    current_scene = None
    current_dialogue = []
    
    for line in lines:
        if line.startswith("SCENE") or line.startswith("EXT.") or line.startswith("INT."):
            # Save previous scene if exists
            if current_scene:
                if current_dialogue:
                    current_scene["dialogue"] = current_dialogue
                scenes.append(current_scene)
                current_dialogue = []
            
            # Start new scene
            current_scene = {
                "heading": line,
                "type": "scene",
                "content": "",
            }
        elif current_scene and line.strip() and not line.strip().isupper():
            if ":" in line and any(role in line for role in ["NARRATOR", "HOST", "CUSTOMER"]):
                parts = line.split(":")
                if len(parts) >= 2:
                    speaker = parts[0].strip()
                    text = ":".join(parts[1:]).strip()
                    current_dialogue.append({
                        "character": speaker,
                        "text": text
                    })
            elif not current_scene["content"]:
                current_scene["content"] = line
            else:
                current_scene["content"] += " " + line
    
    # Add the last scene
    if current_scene:
        if current_dialogue:
            current_scene["dialogue"] = current_dialogue
        scenes.append(current_scene)
    
    return scenes

def show_content_generation():
    """Content Generation page"""
    st.title("Content Generation")
    
    # Progress indicator
    st.markdown("""
    <div class="progress-indicator">
        <div class="progress-step">
            <div class="step-circle active">1</div>
            <div>Content</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">2</div>
            <div>Visual</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">3</div>
            <div>Audio</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">4</div>
            <div>Video</div>
        </div>
        <div class="progress-step">
            <div class="step-circle">5</div>
            <div>Export</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize script in session if not existing
    current_project = st.session_state.current_project
    if current_project not in st.session_state.scripts:
        st.session_state.scripts[current_project] = {
            "title": "",
            "type": "marketing",
            "tone": "professional",
            "target_audience": "",
            "duration": "60",
            "key_points": [],
            "content": "",
            "formatted_content": "",
            "scenes": []
        }
    
    # Content generation tabs
    tabs = st.tabs(["Script Generator", "Script Editor", "Script Preview"])
    
    with tabs[0]:
        st.subheader("Script Generator")
        
        # Script type selection
        script_type = st.selectbox(
            "Script Type",
            ["Marketing Script", "Creative Screenplay", "Explainer Video", "Product Demo"],
            index=0
        )
        
        # Create columns for form inputs
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(
                "Video Title", 
                value=st.session_state.scripts[current_project]["title"],
                key="script_title"
            )
            
            target_audience = st.text_input(
                "Target Audience",
                value=st.session_state.scripts[current_project]["target_audience"],
                key="target_audience"
            )
            
            tone = st.select_slider(
                "Tone",
                options=["Casual", "Professional", "Humorous", "Serious", "Inspirational", "Educational"],
                value=st.session_state.scripts[current_project]["tone"].title(),
                key="tone"
            )
        
        with col2:
            duration = st.slider(
                "Approximate Duration (seconds)",
                min_value=15,
                max_value=300,
                value=int(st.session_state.scripts[current_project]["duration"]),
                step=15,
                key="duration"
            )
            
            # Add product/service details if marketing script
            if script_type == "Marketing Script" or script_type == "Product Demo":
                product_details = st.text_area(
                    "Product/Service Details",
                    key="product_details"
                )
            
            # Call to action
            if script_type == "Marketing Script" or script_type == "Explainer Video":
                call_to_action = st.text_input(
                    "Call to Action",
                    key="call_to_action"
                )
        
        # Key points section
        st.subheader("Key Points")
        st.markdown("Add important points to include in your script:")
        
        key_points = st.session_state.scripts[current_project]["key_points"]
        
        # Display existing key points
        for i, point in enumerate(key_points):
            cols = st.columns([4, 1])
            with cols[0]:
                st.text(f"{i+1}. {point}")
            with cols[1]:
                if st.button("Remove", key=f"remove_{i}"):
                    key_points.pop(i)
                    st.experimental_rerun()
        
        # Add new key point
        new_point = st.text_input("New Point")
        if st.button("Add Point") and new_point:
            key_points.append(new_point)
            st.experimental_rerun()
        
        # Campaign brief for marketing scripts
        if script_type == "Marketing Script" or script_type == "Explainer Video":
            st.subheader("Campaign Brief")
            campaign_brief = st.text_area(
                "Campaign Brief", 
                height=150,
                key="campaign_brief"
            )
        
        # Script generation button
        generate_col1, generate_col2 = st.columns([1, 3])
        with generate_col1:
            if st.button("Generate Script", type="primary"):
                with st.spinner("Generating script..."):
                    # Save form data to session state
                    st.session_state.scripts[current_project]["title"] = title
                    st.session_state.scripts[current_project]["type"] = script_type.lower().replace(" ", "_")
                    st.session_state.scripts[current_project]["tone"] = tone.lower()
                    st.session_state.scripts[current_project]["target_audience"] = target_audience
                    st.session_state.scripts[current_project]["duration"] = str(duration)
                    
                    # Simulate API call with progress
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.02)
                        progress_bar.progress(i + 1)
                    
                    # Generate a mock script based on input
                    if script_type == "Marketing Script":
                        generated_script = generate_marketing_script(
                            title,
                            target_audience,
                            tone.lower(),
                            duration,
                            key_points
                        )
                    elif script_type == "Creative Screenplay":
                        generated_script = generate_creative_screenplay(
                            title,
                            tone.lower(),
                            duration,
                            key_points
                        )
                    elif script_type == "Explainer Video":
                        generated_script = generate_explainer_script(
                            title,
                            target_audience,
                            tone.lower(),
                            duration,
                            key_points
                        )
                    else:  # Product Demo
                        generated_script = generate_product_demo(
                            title,
                            target_audience,
                            tone.lower(),
                            duration,
                            key_points
                        )
                    
                    # Save generated script
                    st.session_state.scripts[current_project]["content"] = generated_script
                    st.session_state.scripts[current_project]["formatted_content"] = format_script(generated_script, script_type)
                    
                    # Parse scenes
                    st.session_state.scripts[current_project]["scenes"] = parse_scenes(generated_script, script_type)
                    
                    # Mark content generation as complete
                    st.session_state.projects[current_project]["progress"]["content_generation"] = True
                    
                    st.success("Script generated successfully!")
        
        with generate_col2:
            st.markdown("""
            **Tip:** For better results, provide detailed key points and be specific about your target audience.
            The more information you provide, the better the generated script will be.
            """)
    
    with tabs[1]:
        st.subheader("Script Editor")
        
        if st.session_state.scripts[current_project]["content"]:
            # Script editor with chat interface
            st.markdown("### Script Editing Assistant")
            st.markdown("Use this assistant to refine your script or ask for suggestions.")
            
            # Display chat history
            chat_container = st.container()
            with chat_container:
                # Initialize chat history if not exists
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []
                
                for message in st.session_state.chat_history:
                    role = message["role"]
                    content = message["content"]
                    
                    if role == "user":
                        st.markdown(f"""
                        <div style='background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>
                            <strong>You:</strong> {content}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='background-color: #e0f7fa; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>
                            <strong>Assistant:</strong> {content}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Input for new message
            user_input = st.text_area("Your message", height=100, key="chat_input")
            
            if st.button("Send", key="send_chat"):
                if user_input:
                    # Add user message to chat history
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": user_input
                    })
                    
                    # Simulate AI response
                    with st.spinner("Assistant is typing..."):
                        time.sleep(1)
                        
                        # Generate mock response based on input
                        if "shorter" in user_input.lower():
                            ai_response = "I've shortened the script while maintaining the key messages. Would you like me to focus on any specific section?"
                        elif "longer" in user_input.lower():
                            ai_response = "I've expanded the script with more details and descriptions. Let me know if you want me to elaborate on any particular part."
                        elif "tone" in user_input.lower():
                            ai_response = "I've adjusted the tone as requested. The script now has a more conversational and engaging style."
                        elif "call to action" in user_input.lower():
                            ai_response = "I've strengthened the call to action at the end of the script to be more compelling and direct."
                        else:
                            ai_response = "I've made the suggested changes to your script. Is there anything specific you'd like me to help with next?"
