import argparse
from distutils.util import strtobool
import os


def parse_args():
    """
    Parses command-line arguments for the Interactive Segmentation Evaluation Pipeline.

    This function defines various options for configuring the evaluation process, including
    model selection, dataset handling, evaluation mode, and hardware settings.

    Returns:
        argparse.Namespace: Parsed command-line arguments with appropriate configurations.
    """
    parser = argparse.ArgumentParser(description="Evaluation Pipeline for Interactive Segmentation")
    
    # General arguments
    parser.add_argument('--network_type', type=str, choices=['DINs', 'SW-FastEdit', 'SimpleClick', 'SAM2', 'MOIS_SAM2'], required=True, help="Type of network to evaluate")
    parser.add_argument('--fold', type=int, choices=[1, 2, 3], required=True, help="Cross-validation fold")
    parser.add_argument('--test_set_id', type=int, choices=[1, 2, 3], required=True, help="Evaluation data subset")
    parser.add_argument('--evaluation_mode', type=str, choices=['lesion_wise_non_corrective', 'lesion_wise_corrective', 'global_corrective'], required=True, help="Evaluation mode")
    
    # Path arguments
    parser.add_argument('--input_dir',type=str, default="/home/gkolokolnikov/PhD_project/nf_segmentation_interactive/NFInteractiveSegmentationBenchmarking/data/raw")
    parser.add_argument('--results_dir',type=str, default="/home/gkolokolnikov/PhD_project/nf_segmentation_interactive/NFInteractiveSegmentationBenchmarkingPrivate/evaluation/results")
    parser.add_argument('--model_weights_dir',type=str, default="/home/gkolokolnikov/PhD_project/nf_segmentation_interactive/NFInteractiveSegmentationBenchmarkingPrivate/model_weights_finetuned")
    parser.add_argument('--checkpoint_name',type=str, default="checkpoint.pt")
    parser.add_argument('--log_dir',type=str, default="/home/gkolokolnikov/PhD_project/nf_segmentation_interactive/NFInteractiveSegmentationBenchmarkingPrivate/evaluation/logs")
   
    # Data arguments
    parser.add_argument("--limit", type=int, default=0, help="Limit the amount of training/validation samples to a fixed number")
    parser.add_argument("--save_predictions", default=False, action="store_true")
    
    # Mode-specific arguments with defaults
    parser.add_argument('--num_lesions', type=int, default=20, help="Number of lesions (default=20)")
    parser.add_argument('--num_interactions_per_lesion', type=int, default=5, help="Interactions per lesion (default=5)")
    
    # Set of fixed arguments
    parser.add_argument("--use_gpu", default=False, action="store_true")
    parser.add_argument("--interaction_probability", type=float, default=1.0)
    parser.add_argument("--sigma", type=int, default=1)
    parser.add_argument("--no_disks", default=False, action="store_true")
    
    # Cache arguments
    parser.add_argument("--cache_dir", type=str, default="/home/gkolokolnikov/PhD_project/nf_segmentation_interactive/NFInteractiveSegmentationBenchmarkingPrivate/evaluation/cache")
    parser.add_argument("--throw_away_cache", default=False, action="store_true", help="Use a temporary folder which will be cleaned up after the program run.")
    
    # MOIS SAM2-specific arguments with defaults
    parser.add_argument('--exemplar_use_com', type=lambda x: bool(strtobool(x)), default=True, help="Use exemplar-based segmentation to define center of masses.")
    parser.add_argument('--exemplar_use_only_prompted', type=lambda x: bool(strtobool(x)), default=False, help="Use only prompted exemplars.")
    parser.add_argument('--exemplar_inference_all_slices', type=lambda x: bool(strtobool(x)), default=True, help="Use exemplar-based segmentation in all slices of an image.")
    parser.add_argument('--exemplar_num', type=int, default=8, help="Number of exemplars to use in the exemplar-based segmentation")
    parser.add_argument('--filter_prev_prediction_components', type=lambda x: bool(strtobool(x)), default=True, help="Filter exemplar-based prediction according to the prompt-based results.")
    parser.add_argument('--use_low_res_masks_for_com_detection', type=lambda x: bool(strtobool(x)), default=True, help="Use low-resulution semantic mask for detecting centers of mass of lesions.")
    parser.add_argument('--min_lesion_area_threshold', type=int, default=40, help="Minimal area of potential of lesion predicted with exemplars")
    parser.add_argument('--no_prop_beyond_lesions', type=lambda x: bool(strtobool(x)), default=True, help="Do not perform exemplar-based propagation if all lesions were processed with interactions.")

    args = parser.parse_args()
    
    # Derived arguments based on evaluation mode
    if args.evaluation_mode == 'lesion_wise_non_corrective':
        args.num_interactions_per_lesion = 1
        args.num_interactions_total_max = args.num_lesions
        args.dsc_local_max = 1.0
        args.dsc_global_max = 1.0

    elif args.evaluation_mode == 'lesion_wise_corrective':
        args.num_interactions_total_max = args.num_lesions * args.num_interactions_per_lesion
        args.dsc_local_max = 1.0
        args.dsc_global_max = 1.0

    elif args.evaluation_mode == 'global_corrective':
        args.num_lesions = 1
        args.num_interactions_total_max = args.num_interactions_per_lesion
        args.dsc_local_max = 0.8
        args.dsc_global_max = 0.8
        
    # Derived arguments based on network type
    args.model_dir = os.path.join(args.model_weights_dir, args.network_type, f"fold_{args.fold}")
    
    if args.network_type == "SW-FastEdit":
        args.checkpoint_name = "checkpoint.pt"
        args.sw_batch_size = 4
        args.patch_size_discrepancy = (512, 512, 16)
        args.non_standard_network = False
    elif args.network_type == "DINs":
        args.checkpoint_name = "checkpoint.onnx"
        args.non_standard_network = True
        args.patch_size_discrepancy = (256, 128, 10)
        args.sw_batch_size = 4
        args.no_disks = True
        args.sigma=(5.0, 5.0, 1.0)
    elif args.network_type == "SimpleClick":
        args.checkpoint_name = "checkpoint_simpleclick.pth"
        args.checkpoint_propagator = "checkpoint_stcn.pth"
        args.non_standard_network = True
        args.patch_size_discrepancy = (512, 512, 16)
    elif args.network_type == "SAM2":
        args.checkpoint_name = "checkpoint.pt"
        args.config_name = "sam2.1_hiera_b+.yaml"
        args.non_standard_network = True
        args.patch_size_discrepancy = (512, 512, 16)
    elif args.network_type == "MOIS_SAM2":
        args.checkpoint_name = "checkpoint.pt"
        args.config_name = "mois_sam2.1_hiera_b+.yaml"
        args.non_standard_network = True
        args.patch_size_discrepancy = (512, 512, 16)     
        
    # Default labels
    args.labels = {"lesion": 1, "background": 0}
    args.include_background_in_metric = False

    return args
