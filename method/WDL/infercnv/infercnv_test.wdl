workflow infercnv {
    File matrix_file
    File gene_pos_file
    File metadata_file
    String output_dir
    String diskSpace
    String delimiter
    # String cluster_names
    String ref_cluster_name
    String ref_group_name
    File ref_cluster_file # Path to cluster file containing reference (normal) cells
    String obs_cluster_name
    File obs_cluster_file # Path to cluster file containing observation (tumor) cells
    String reference_cell_annotation
    String observation_cell_annotation
    
    call run_infercnv {
    	input:
        matrix_file = matrix_file,
        gene_pos_file = gene_pos_file,
        output_dir = output_dir,
        diskSpace = diskSpace,
        delimiter = delimiter,
        # cluster_path = cluster_path
        ref_cluster_name = ref_cluster_name,
        ref_cluster_file = ref_cluster_file,
        obs_cluster_name = obs_cluster_name,
        obs_cluster_file = obs_cluster_file,
        metadata_file = metadata_file,
        reference_cell_annotation = reference_cell_annotation,
        observation_cell_annotation = observation_cell_annotation
    }
    
    call run_matrix_to_ideogram_annots {
    	input:
        matrix_file = run_infercnv.observations_matrix_file,
        ref_group_names_file = run_infercnv.ref_group_names_file,
        heatmap_thresholds_file = run_infercnv.heatmap_thresholds_file,
        gene_pos_file = gene_pos_file,
        # cluster_names = cluster_names,
        # cluster_path = cluster_path,
        ref_cluster_name = ref_cluster_name,
        ref_cluster_file = ref_cluster_file,
        obs_cluster_name = obs_cluster_name,
        obs_cluster_file = obs_cluster_file,
        ref_group_name = ref_group_name,
        metadata_file = metadata_file,
        diskSpace = diskSpace,
        output_dir = output_dir
    }
}

task run_infercnv {
    File matrix_file
    File gene_pos_file
    String output_dir
    String diskSpace
    String delimiter
    String ref_cluster_name
    File ref_cluster_file
    String obs_cluster_name
    File obs_cluster_file
    File metadata_file
    String reference_cell_annotation
    String observation_cell_annotation

    command <<<
        if [ ! -d ${output_dir} ]; then
            mkdir -p ${output_dir}
        fi
        
        # Convert SCP files into inferCNV annotations file
        python3 /single_cell_portal/scripts/scp_to_infercnv.py \
            --metadata-path ${metadata_file} \
            --reference-cluster-path ${ref_cluster_file} \
            --reference-group-name ${reference_cell_annotation} \
            --observation-group-name ${observation_cell_annotation} \
            --output-dir ${output_dir}
        # Outputs:
        #   infercnv_reference_cell_labels_from_scp.tsv
        #   infercnv_annots_from_scp.tsv
        
        # Convert matrix as needed
        python3 /inferCNV/scripts/check_matrix_format.py \
            --input_matrix ${matrix_file} \
            --delimiter $'${delimiter}' \
            --output_name "${output_dir}/expression.r_format.txt"
        
        # Run inferCNV
        inferCNV.R \
            --raw_counts_matrix "${output_dir}/expression.r_format.txt" \
            --annotations_file "${output_dir}/infercnv_annots_from_scp.tsv" \
            --gene_order_file ${gene_pos_file} \
            --ref_group_names "`cat ${output_dir}/infercnv_reference_cell_labels_from_scp.tsv`" \
            --cutoff 1 \
            --delim $'${delimiter}' \
            --out_dir ${output_dir} \
            --cluster_by_groups \
            --denoise \
            --no_prelim_plot
        >>>
    output {
        File figure = "${output_dir}/infercnv.png"
        File observations_matrix_file = "${output_dir}/infercnv.observations.txt"
        File heatmap_thresholds_file = "${output_dir}/infercnv.heatmap_thresholds.txt"
        File ref_group_names_file = "${output_dir}/infercnv_reference_cell_labels_from_scp.tsv"
    }

    # runtime {
    # 	# https://hub.docker.com/r/singlecellportal/infercnv/tags
    #     docker: "singlecellportal/infercnv:0-8-2-rc11"
    #     memory: "8 GB"
    #     bootDiskSizeGb: 12
    #     disks: "local-disk ${diskSpace} HDD"
    #     cpu: 8
    #     preemptible: 2
    # }
}

task run_matrix_to_ideogram_annots {
	File matrix_file
    File ref_group_names_file
    File gene_pos_file
    # String cluster_names
    # File cluster_paths
    String ref_cluster_name
    File ref_cluster_file
    String obs_cluster_name
    File obs_cluster_file
    File metadata_file
    File heatmap_thresholds_file
    String output_dir
    String diskSpace
    String ref_group_name
    
    command <<<
        if [ ! -d ${output_dir} ]; then
           mkdir -p ${output_dir}
        fi

        # Convert processed matrix output from inferCNV to summary Ideogram.js annotations
        python3 /single_cell_portal/scripts/ideogram/matrix_to_ideogram_annots.py \
            --matrix-path ${matrix_file} \
            --matrix-delimiter $' ' \
            --gen-pos-file ${gene_pos_file} \
            --cluster-names "${obs_cluster_name}" \
            --ref-cluster-names "`cat ${ref_group_names_file}`" \
            --cluster-paths "${obs_cluster_file}" \
            --metadata-path ${metadata_file} \
            --heatmap-thresholds-path ${heatmap_thresholds_file} \
            --output-dir ${output_dir} \
            --reference-group-name "${ref_group_name}"
    >>>
    
	output {
    # Array[File] ideogram_annotations = glob("${output_dir}/ideogram_exp_means/*.json") # Fails, cause unknown

    # TODO: Fix above glob expression, discard the less flexible expression below
    File ideogram_annotations = "${output_dir}/ideogram_exp_means/ideogram_exp_means__${obs_cluster_name}--${ref_group_name}--group--cluster.json"
  }

	# runtime {
  #   	# https://hub.docker.com/r/singlecellportal/infercnv/tags
  #       docker: "singlecellportal/infercnv:0-8-2-rc11"
  #       memory: "8 GB"
  #       bootDiskSizeGb: 12
  #       disks: "local-disk ${diskSpace} HDD"
  #       cpu: 8
  #       preemptible: 2
  #   }
}